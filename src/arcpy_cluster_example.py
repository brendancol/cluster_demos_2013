import json
import multiprocessing
import os
import unittest

from collections import defaultdict

import arcpy

from decorator_utils import standardErrorLoggging, logArgs

@standardErrorLoggging
def cluster_worker(sourcePointFeatureClass, outputDirectory, levelInfos=None, whereClause=None, workerName=None, includeLevels=None):
	print '.rectify_worker({})'.format(workerName)
	arcpy.env.overwriteOutput = True
	outputGeodatabaseName = "temp{}.gdb".format(workerName)
	outputGeodatabase = os.path.join(outputDirectory, outputGeodatabaseName)
	if arcpy.Exists(outputGeodatabase):
		arcpy.Delete_management(outputGeodatabase)
	arcpy.CreateFileGDB_management(outputDirectory, outputGeodatabaseName)
	arcpy.env.workspace = outputGeodatabase

	points_feature_layer = 'temp_points'
	points_feature_class = 'source_points'
	
	arcpy.MakeFeatureLayer_management(sourcePointFeatureClass, points_feature_layer, whereClause)
	arcpy.CopyFeatures_management(points_feature_layer, points_feature_class)

	level_infos_json = """{"origin":{"x":-20037508.342787,"y":20037508.342787},"spatialReference":{"wkid":102100},"lods":[{"level":0,"resolution":156543.033928,"scale":591657527.591555},{"level":1,"resolution":78271.5169639999,"scale":295828763.795777},{"level":2,"resolution":39135.7584820001,"scale":147914381.897889},{"level":3,"resolution":19567.8792409999,"scale":73957190.948944},{"level":4,"resolution":9783.93962049996,"scale":36978595.474472},{"level":5,"resolution":4891.96981024998,"scale":18489297.737236},{"level":6,"resolution":2445.98490512499,"scale":9244648.868618},{"level":7,"resolution":1222.99245256249,"scale":4622324.434309},{"level":8,"resolution":611.49622628138,"scale":2311162.217155},{"level":9,"resolution":305.748113140558,"scale":1155581.108577},{"level":10,"resolution":152.874056570411,"scale":577790.554289},{"level":11,"resolution":76.4370282850732,"scale":288895.277144},{"level":12,"resolution":38.2185141425366,"scale":144447.638572},{"level":13,"resolution":19.1092570712683,"scale":72223.819286},{"level":14,"resolution":9.55462853563415,"scale":36111.909643},{"level":15,"resolution":4.77731426794937,"scale":18055.954822},{"level":16,"resolution":2.38865713397468,"scale":9027.977411},{"level":17,"resolution":1.19432856685505,"scale":4513.988705},{"level":18,"resolution":0.597164283559817,"scale":2256.994353},{"level":19,"resolution":0.298582141647617,"scale":1128.497176}],"units":"esriMeters"}"""
	level_infos = json.loads(unicode(level_infos_json, 'latin-1'))
	clustered_feature_classes = []
	for level_info in level_infos['lods']:
		if not includeLevels or int(level_info['level']) in includeLevels:
			cluster_feature_class = create_cluster_layer(points_feature_class, level_info)
			if cluster_feature_class:
				clustered_feature_classes.append(os.path.join(outputGeodatabase, cluster_feature_class))
	return (clustered_feature_classes, workerName, outputGeodatabase)

@standardErrorLoggging
def create_cluster_layer(sourcePointFeatureClass, levelInfo):
	level, res = (levelInfo['level'], levelInfo['resolution'])

	integrate_name = 'integrate_{}'.format(level)
	arcpy.CopyFeatures_management(sourcePointFeatureClass, integrate_name)

	distance = "{} Meters".format(res * 10)
	try:
		arcpy.Integrate_management(integrate_name, distance)
	except:
		message = arcpy.GetMessage(0)
		if 'maximum tolerance exceeded' in message.lower():
			print 'maximum tolerance exceeded: {} - {}'.format(integrate_name, distance)
			return None
		else:
			raise

	cluster_name = 'clusters_{}'.format(level)
	cluster_features = arcpy.CollectEvents_stats(integrate_name, cluster_name)

	output_name = 'clusters_{}_joined'.format(level)
	add_attributes(integrate_name, cluster_name, output_name, )

	arcpy.Delete_management(integrate_name)
	arcpy.Delete_management(cluster_name)

	arcpy.AddField_management(output_name, 'zoom_level', "SHORT")
	expression = "int({})".format(levelInfo['level'])
	arcpy.CalculateField_management(output_name, 'zoom_level', expression, "PYTHON")

	return output_name

@standardErrorLoggging
def add_attributes(integratedFeatureClass, clustersFeatureClass, outputFeatureClass, mergeNumericFields=[], mergeTextFields=False):
	'''
	TODO: Add join option for string fields; 
	TOOD: Add customizable fields for summary

	summarizes attributes for clusters
	First - The first input value is used.
	Last -The last input value is used.
	Join -Merge the values together using the delimiter value to separate the values (only valid if the output field type is text).
	Min -The smallest input value is used (only valid if the output field type is numeric).
	Max -The largest input value is used (only valid if the output field type is numeric).
	Mean -The mean is calculated using the input values (only valid if the output field type is numeric).
	Median -The median is calculated using the input values (only valid if the output field type is numeric).
	Sum -The sum is calculated using the input values (only valid if the output field type is numeric).
	StDev -The standard deviation is calculated using the input values (only valid if the output field type is numeric).
	Count -The number of values included in statistical calculations. This counts each value except null values.
	'''
	fieldmappings = arcpy.FieldMappings()
	fieldmappings.addTable(clustersFeatureClass)

	integrated_fields = arcpy.ListFields(integratedFeatureClass)
	for f in integrated_fields:
		if f.type in ['Integer', 'SmallInteger', 'Double', 'Single']:
			template = f.name + '_{}'
			for m in ['Min', 'Max', 'Mean', 'Sum', 'Count', 'StDev', 'Median']:
				fieldmap = arcpy.FieldMap()
				fieldmap.addInputField(integratedFeatureClass, f.name)
				field = fieldmap.outputField
				field.name = template.format(m.lower())
				field.aliasName = template.format(m.lower())
				fieldmap.mergeRule = m
				fieldmap.outputField = field
				fieldmappings.addFieldMap(fieldmap)

	arcpy.SpatialJoin_analysis(clustersFeatureClass, integratedFeatureClass, outputFeatureClass, "#", "#", fieldmappings)

@standardErrorLoggging
def create_membership_where(featureClass, fieldName, values):
	where_membership = ','.join(["'{}'".format(v) for v in values])
	return arcpy.AddFieldDelimiters(featureClass, fieldName) + " IN ({})".format(where_membership)

@standardErrorLoggging
def get_unique_field_values(featureClass, fieldName, where=None, getValueFunction=None):
	unique_values = []
	with arcpy.da.SearchCursor(featureClass, [fieldName], where) as cursor:
		for r in cursor:
			if getValueFunction:
				unique_values.append(getValueFunction(r[0]))
			else:
				unique_values.append(str(r[0]))
	final_list = list(set(unique_values))
	return final_list

all_results = []
delete_files = []
@standardErrorLoggging
def cluster_complete(results):
	clustered_feature_classes, workerName, delete_file = results
	print 'worker complete({})'.format(workerName)

	global all_results
	global delete_files

	all_results += clustered_feature_classes
	delete_files.append(delete_file)

@standardErrorLoggging
def run_clustering(featureClass, clusterField, outputDirectory, includeLevels=None):
	global all_results
	global delete_files
	arcpy.gp.overwriteOutput = True
	pool = multiprocessing.Pool(multiprocessing.cpu_count() - 1)
	for v in get_unique_field_values(featureClass, clusterField):
		where = create_membership_where(featureClass, clusterField, [v])
		worker_arguments = (featureClass, outputDirectory, None, where, v, includeLevels)
		pool.apply_async(cluster_worker, worker_arguments, callback=cluster_complete)
	pool.close()
	pool.join()

	final_output = featureClass + '_clustered'
	arcpy.CopyFeatures_management(all_results.pop(), final_output)
	arcpy.Append_management(all_results, final_output, "TEST")

	for d in delete_files:
		arcpy.Delete_management(d)

#=============================================================================================================
# TESTING
#=============================================================================================================
class TestClustering(unittest.TestCase):
	def test_run_clustering(self):
		feature_class = 'C:\gis_working_directory\school_clustering.gdb\CCD_10_11_WM'
		clusterField = 'lstate'
		outputDirectory = 'C:\gis_working_directory'
		levels = range(4, 16)
		run_clustering( feature_class, clusterField, outputDirectory, includeLevels=levels )

	def _add_attributes(self):
		arcpy.gp.overwriteOutput = True
		integrated_feature_class = r'C:\gis_working_directory\tempDE.gdb\integrate_10'
		clusters = r'C:\gis_working_directory\tempDE.gdb\clusters_10'
		outputDirectory = r'C:\gis_working_directory\tempDE.gdb\clusters_10_joined'
		add_attributes(integrated_feature_class, clusters, outputDirectory)

if __name__ == '__main__':
	unittest.main()
