import arcpy
import os
import types

from collections import defaultdict
from decorator_utils import logArgs, standardErrorLoggging

@standardErrorLoggging(logger=logger)
def stripFieldValues(featureClass, stringFields):
	with arcpy.da.UpdateCursor(featureClass, [stringFields]) as updateCursor:
		for r in updateCursor:
			for i, s in enumerate(stringFields):
				if r[i] and not r[i] == r[i].strip():
					r[i] = r[i].strip()
					updateCursor.updateRow(r)

@standardErrorLoggging(logger=logger)
def summarizeArea(featureClass, where='1=1'):
	total_area = 0
	with arcpy.da.SearchCursor(featureClass, ['SHAPE@AREA'], where) as cursor:
		for c in cursor:
			total_area += c[0]
	return total_area

@standardErrorLoggging(logger=logger)
def getUnionedFeatures(featureClass, where='1=1'):
	union_polygon = None
	with arcpy.da.SearchCursor(featureClass, ['SHAPE@'], where) as cursor:
		for c in cursor:
			if not union_polygon:
				union_polygon = c[0]
			else:
				union_polygon = union_polygon.union(c[0])
	return union_polygon
			
@standardErrorLoggging(logger=logger)
def compareSchemas(featureClassOne, featureClassTwo):

	#Just added this in because tool needed it...this is just a schema compare...
	fieldnames = [f.name for f in arcpy.ListFields(featureClassOne)]
	sort_field = fieldnames[0]

	compare_result = arcpy.TableCompare_management(featureClassOne, featureClassTwo, [sort_field], 'SCHEMA_ONLY')
	return compare_result.getOutput(0)

@standardErrorLoggging(logger=logger)
def createStringIndex(inputFeatureClass, keyField, valueField, fields=None, keyFunction=None, valueFunction=None, where=None):
	if not fields:
		fields = [keyField, valueField]

	if not keyFunction:
		keyFunction = lambda row:row[0]
	
	if not valueFunction:
		valueFunction = lambda row:row[1]
		
	index = {}
	with arcpy.da.SearchCursor(inputFeatureClass, fields, where) as cursor:
		for row in cursor:
			index[keyFunction(row)] = valueFunction(row)
	return index

@standardErrorLoggging(logger=logger)
def createListIndex(items, keyFunction, valueFunction):
	listIndex = defaultdict(list)
	for i in items:
		listIndex[keyFunction(i)].append(valueFunction(i))
	return listIndex

@standardErrorLoggging(logger=logger)
def indexDictList(keyFunction, valueFunction, sourceDictList):
	index = {}
	for d in sourceDictList:
		index[keyFunction(d)] = valueFunction(d)
	return index

@standardErrorLoggging(logger=logger)
def getUniqueFieldValues(featureClass, fieldName, where=None, getValueFunction=None):
	unique_values = []
	with arcpy.da.SearchCursor(featureClass, [fieldName], where) as cursor:
		for r in cursor:
			if getValueFunction:
				unique_values.append(getValueFunction(r[0]))
			else:
				unique_values.append(str(r[0]))
	final_list = list(set(unique_values))
	return final_list

@standardErrorLoggging(logger=logger)
def createStringMembershipWhereClause(featureClass, fieldName, values):
	where_membership = ','.join(["'{}'".format(v) for v in values])
	return arcpy.AddFieldDelimiters(featureClass, fieldName) + " IN ({})".format(where_membership)

@standardErrorLoggging(logger=logger)
def createStringCompareWhereClause(featureClass, fieldName, value, operator='='):
	return arcpy.AddFieldDelimiters(featureClass, fieldName) + " {} '{}'".format(operator, value)

@standardErrorLoggging(logger=logger)
def assertFeatureCount(featureLayer, minimum=None, maximum=None, exactly=None):
	count = int(arcpy.GetCount_management(featureLayer).getOutput(0))
	if minimum and count < minimum:
		raise Exception('ERROR: Layer {} must have at least {} features, but has {}.'.format(featureLayer, minimum, count))
	elif maximum and count > maximum:
		raise Exception('ERROR: Layer {} must have at most {} features, but has {}.'.format(featureLayer, maximum, count))
	elif exactly and count != exactly:
		raise Exception('ERROR: Layer {} must have exactly {} features, but has {}.'.format(featureLayer, exactly, count))
	return count

@standardErrorLoggging(logger=logger)
def getFeatureCount(inputFeatureClass):
	return int(arcpy.GetCount_management(inputFeatureClass).getOutput(0))

@standardErrorLoggging(logger=logger)
def cursorRowsAsDicts(cursor):
	colnames = cursor.fields
	for row in cursor:
		arcpy.AddMessage(str(row))

		d = dict(zip(colnames, row))
		arcpy.AddMessage(d)
		yield d

@standardErrorLoggging(logger=logger)
def getCursorCount(inputFeatureClass, fields, whereClause):
	'''
	very sad hack around getting the row count of a cursor
	'''

	count = 0
	with arcpy.da.SearchCursor(inputFeatureClass, fields, whereClause) as cursor:
		for r in cursor:
			count += 1
	return count
	
@standardErrorLoggging(logger=logger)
def fixLeadingZeroFields(inputFeatureClass, fieldName, length):
	
	temp_field = fieldName + '_temp'
	
	#Add in District Id Field
	arcpy.AddField_management(inputFeatureClass, 
							  temp_field,
							  "text", 
							  length)
	
	calc_expression = "str(!" + fieldName + "!)" + ".zfill(" + str(length) +")" 
	arcpy.CalculateField_management(inputFeatureClass, 
									fieldName + '_temp', 
									calc_expression,
									"PYTHON")
	
	arcpy.DeleteField_management(inputFeatureClass, [fieldName])
	
	#Add in District Id Field
	arcpy.AddField_management(inputFeatureClass, 
							  fieldName,
							  "text", 
							  length)
	
	calc_expression = "!" + temp_field + "!" 
	arcpy.CalculateField_management(inputFeatureClass, 
									fieldName, 
									calc_expression,
									"PYTHON")
	
	#arcpy.DeleteField_management(inputFeatureClass, [temp_field])
@logArgs(logger=logger) 
@standardErrorLoggging(logger=logger)        
def getCommonFieldNames(featureClasses):
	common_names = []
	for fc in featureClasses:
		fields = arcpy.ListFields(fc)
		names = [f.name for f in fields if f.editable]
		common_names.append(set(names))
		del fields
	return set.intersection(*common_names)

@logArgs(logger=logger) 
@standardErrorLoggging(logger=logger)        
def hasField(inputFeatureClass, fieldName):
	fields = arcpy.ListFields(inputFeatureClass)
	names = [f.name for f in fields]
	del fields
	return fieldName in names

@standardErrorLoggging(logger=logger)
def assertUniformProjections(featureClasses):
	proj_matches = defaultdict(list)
	for f in featureClasses:
		proj_matches[arcpy.Describe(f).spatialReference.name].append(f)

	if len(proj_matches.keys()) > 1:
		message = ''
		for k,v in proj_matches.items():
			message += '\n\n\tProjection information does not match {} --> '.format(k, '; '.join(v))
		raise Exception(message)

@standardErrorLoggging(logger=logger)
def assertUniformGeometryType(featureClasses, shapeType=None):
	fail = False
	error_message = ''
	shape_type_matches = defaultdict(list)
	for f in featureClasses:
		actual_type = arcpy.Describe(f).shapeType
		if shapeType and shapeType.lower() != actual_type.lower():
			fail = True
			error_message += 'n\tShape type mismatch {} is {} but should be {}'.format(f, actual_type, shapeType)
		else:
			shape_type_matches[actual_type].append(f)
	if len(shape_type_matches.keys()) > 1:
		message = ''
		for k,v in shape_type_matches.items():
			fail = True
			error_message += '\n\tShape types do not match {} --> '.format(k, '; '.join(v))
	if fail:
		raise Exception(error_message)

@standardErrorLoggging(logger=logger)
def assertFieldAttributeDomain(featureClass, fieldDomainLookup={}, where=None):
	'''
	The fieldDomainLookup is a dictionary (fieldname : list<acceptable_values>).

	Returns a dictionary (fieldname : list<error_values>).
	'''
	fields = fieldDomainLookup.keys()
	fieldErrors = defaultdict(list)
	with arcpy.da.SearchCursor(inputFeatureClass, fields, where) as cursor:
		for r in cursor:
			for i,f in enumerate(fields):
				val = r[i]
				if val not in fieldDomainLookup[f]:
					fieldErrors[f].append(val)
	return fieldErrors

def assertFieldValuesExist(featureClass, fieldValuesLookup={}, where=None):
	'''
	fieldValuesLookup => dictionary (fieldname : list<values_which_must_exist>).

	Returns => dictionary (fieldname : list<error_values>).
	'''
	fields_verified = defaultdict(dict)
	for field, values in fieldValuesLookup.items():
		for value in values:
			fields_verified[field][value] = False 

	fields = fieldValuesLookup.keys()
	with arcpy.da.SearchCursor(featureClass, fields, where) as cursor:
		for r in cursor:
			for i, f in enumerate(fields):
				val = r[i]
				if val in fieldValuesLookup[f]:
					fields_verified[f][val] = True

	fieldErrors = defaultdict(list)
	for field, verifiedValues in fields_verified.items():
		for fieldValue, verified in verifiedValues.items():
			if not verified:
				fieldErrors[field].append(fieldValue)

	return fieldErrors

def assertField(featureClass, fieldName):
	if not hasField(featureClass, fieldName):
		raise Exception('\n\n\t{} field not found in feature class: {}'.format(fieldName, featureClass))

def assertFields(featureClass, fieldNames):
	for f in fieldNames:
		if not hasField(featureClass, f):
			raise Exception('\n\n\t{} field not found in feature class: {}'.format(f, featureClass))

def assertExists(inputFeatureClasses):
	for f in inputFeatureClasses:
		if not arcpy.Exists(f):
			raise Exception('\n\n\t Feature class does not exist {}'.format(f))

@logArgs(logger=logger) 
@standardErrorLoggging(logger=logger) 
def assertNoEmptyValues(inputFeatureClasses, fieldName, where=None, domain=None):
	def check(row, domain=None):
		if not row[0]:
			raise Exception('\n\n\t<b>{} (fieldname = {}): Cannot contain null or empty values'.format(currentFeatureClass, fieldName))
		if domain:
			if row[0] not in domain:
				raise Exception('\n\n\t<b>{} (fieldname = {}): Value ({}) Outside Domain: {}}'.format(currentFeatureClass, fieldName, r[0], domain))
		
	currentFeatureClass = None
	for f in inputFeatureClasses:
		currentFeatureClass = f
		mapRows2(currentFeatureClass, [fieldName], where, [check])
	
@logArgs(logger=logger)
@standardErrorLoggging(logger=logger)          
def transferField(fromFeatureClass, toFeatureClass, fieldName):
	'''
	Calls AddField based on field from other feature class
	'''
	inputFields = arcpy.ListFields(fromFeatureClass)
	fieldFound = False
	for f in inputFields:
		if f.name.strip() == fieldName.strip():
			fieldFound = True
			arcpy.AddMessage(f.name + ' >>> ' + fieldName + ' >>> ' + str(f.name.strip() == fieldName.strip()))
			arcpy.AddField_management(toFeatureClass, f.name, f.type, f.precision, f.scale, f.length, f.aliasName, f.isNullable, f.required, f.domain)
			return
	
	if not fieldFound:
		raise Exception('Transfer field could not find requested field name')

@logArgs(logger=logger)
@standardErrorLoggging(logger=logger)  
def setupOutputFeatureClass(outputPath, template, geometryType=None, spatial_reference=None, overwriteOutput=False):
	'''
	setting overwriteOutput to True will delete feature class if it already exists.
	'''
	if overwriteOutput and arcpy.Exists(outputPath):
		arcpy.Delete_management(outputPath)

	if not geometryType:
		geometryType = arcpy.Describe(template).shapeType.upper()

	if not spatial_reference:
		spatial_reference = arcpy.Describe(template).spatialReference
		
	outLocation = os.path.split(outputPath)[0]
	outName = os.path.split(outputPath)[1]
	arcpy.CreateFeatureclass_management(outLocation, outName, geometryType, template, spatial_reference=spatial_reference)
	return outputPath

@logArgs(logger=logger)
@standardErrorLoggging(logger=logger)  
def translateAppend(targetFeatureClass, appendFeatureClass, where, fieldTranslations, outputFeatureClass):
	import types
	
	arcpy.CopyFeatures_management(targetFeatureClass, outputFeatureClass)
	insertCursor = arcpy.InsertCursor(outputFeatureClass)
	appendRows = arcpy.SearchCursor(appendFeatureClass, where)
	
	for r in appendRows:
		newRow = insertCursor.newRow() 
		for k,v in fieldTranslations.items():
			value = None
			if isinstance(v, types.FunctionType):
				value = v(r)
			else:
				value = r.getValue(v)
			if value:
				newRow.setValue(k, value)
		insertCursor.insertRow(newRow)
	
	del newRow
	del appendRows
	del insertCursor

@logArgs(logger=logger)
@standardErrorLoggging(logger=logger)  
def mapRows(featureClass, where, functionList):
	rows = arcpy.SearchCursor(featureClass, where)
	for r in rows:
		for f in functionList:
			f(r)
	del rows

@logArgs(logger=logger)
@standardErrorLoggging(logger=logger)
def mapRows2(featureClass, fields, where, functionList):
	with arcpy.da.SearchCursor(featureClass, fields, where) as rows:
		for r in rows:
			for f in functionList:
				f(r)

@logArgs(logger=logger)
@standardErrorLoggging(logger=logger)
def groupRows(inputFeatureClass, where, keyFunction, valueFunction):
	from collections import defaultdict

	groupings = defaultdict(list)
	rows = arcpy.SearchCursor(inputFeatureClass, where)
	for r in rows:
		groupings[keyFunction(r)].append(valueFunction(r))
	del rows
	return groupings

@logArgs(logger=logger)
@standardErrorLoggging(logger=logger)
def groupRows2(inputFeatureClass, fields, where, keyFunction, valueFunction):
	from collections import defaultdict
	groupings = defaultdict(list)
	with arcpy.da.SearchCursor(inputFeatureClass, fields, where) as cursor:
		for r in cursor:
			groupings[keyFunction(r)].append(valueFunction(r))
	return groupings

@logArgs(logger=logger)
@standardErrorLoggging(logger=logger)  
def transposeRows(targetFeatureClass, outputFeatureClass):
	nonTransposeFields = []
	transposeItems = defaultdict(list)
	fieldNamePredicates = []
	deleteFields = []
	
	fields = arcpy.ListFields(targetFeatureClass)
	for f in fields:
		try:
			lastNumber = int(f.name[-1])
			if lastNumber == 0:
				nonTransposeFields.append(f.name)
				continue
			else:
				transposeItems[lastNumber].append(f.name)
				fieldNamePredicates.append(f.name[:-1])
				if not f.required: deleteFields.append(f.name)
		except ValueError:
			nonTransposeFields.append(f.name)
	
	setupOutputFeatureClass(outputFeatureClass, targetFeatureClass)
	
	fieldNamePredicates = set(fieldNamePredicates) 
	for p in fieldNamePredicates:
		arcpy.AddField_management(outputFeatureClass, p, "text", "255")
		
	insertCursor = arcpy.InsertCursor(outputFeatureClass)
	appendRows= arcpy.SearchCursor(targetFeatureClass)
	for r in appendRows:
		for k,v in transposeItems.items():
			idCheck = False
			gradeCheck = False
			for fieldName in v:

				if fieldName.startswith('NCESSCH') and r.getValue(fieldName).strip():
					idCheck = True
					continue
				
				if fieldName.startswith('GS') and r.getValue(fieldName).strip().lower() not in ['ug', 'n']:
					gradeCheck = True
					continue
			
			if idCheck and gradeCheck:
				newRow = insertCursor.newRow()
				for n in nonTransposeFields:
					if n.lower() in ['objectid', 'shape_length', 'shape_area']:
						continue
					
					newRow.setValue( n, r.getValue(n))
				
				for f in v:
					predicate = f[:-1]
					newRow.setValue(predicate, r.getValue(f))
					
				insertCursor.insertRow(newRow)
				
	del newRow
	del appendRows
	del insertCursor
	
	arcpy.DeleteField_management(outputFeatureClass, deleteFields)

@standardErrorLoggging(logger=logger)
def getNullCountsByField(inputFeautreClass):
	counts = {}
	fields = arcpy.ListFields(inputFeautreClass)
	names = [f.name for f in fields]
	for n in names:
		counts[n] = 0
		
	rows = arcpy.SearchCursor(inputFeautreClass)
	for r in rows:
		for n in names:
			if not r.getValue(n):
				counts[n] += 1
	
	return counts
	
@logArgs(logger=logger)
@standardErrorLoggging(logger=logger)         
def getSDEFeatureClassPath(connectionFile, sdePrefix, featureClass, featureDataset=None):
	
	returnPath = os.path.join(connectionFile,sdePrefix)
	if(featureDataset):
		returnPath = getSDEFeatureDatasetPath(connectionFile, sdePrefix, featureDataset)
		returnPath = os.path.join(returnPath, sdePrefix)
	
	return '.'.join([returnPath, featureClass])
	
@logArgs(logger=logger)
@standardErrorLoggging(logger=logger)          
def getSDEFeatureDatasetPath(connectionFile, sdePrefix, featureDataset=None):
	return os.path.join(connectionFile, sdePrefix) + '.' + featureDataset


@logArgs(logger=logger)
@standardErrorLoggging(logger=logger)  
def filterFeatures(inputFeatureClass, outputFeatureClass, whereClause):   
	
	#Stupid hack for arcpy search cursor row count.
	inputRows = arcpy.SearchCursor(inputFeatureClass, whereClause)
	count = 0
	for i in inputRows:
		count+=1
		break
	del inputRows

	if count == 0:
		return
	
	setupOutputFeatureClass(outputFeatureClass, inputFeatureClass)

	inputRows = arcpy.SearchCursor(inputFeatureClass, whereClause)
	outputRows = arcpy.InsertCursor(outputFeatureClass)

	for r in inputRows:
		outputRows.insertRow(r)

	del inputRows
	del outputRows

@standardErrorLoggging(logger=logger) 
def getGeometryFieldName(featureClass):
	return arcpy.Describe(featureClass).shapeFieldName

@standardErrorLoggging(logger=logger)  
def getNonGeometryFieldNames(featureClass):
	'''
	Returns all fieldnames except for geometry fields
	'''
	fieldnames = []
	fields = arcpy.ListFields(featureClass)
	for f in fields:
		if f.type != 'Geometry':
			fieldnames.append(f.name)
	return fieldnames

@logArgs(logger=logger)
@standardErrorLoggging(logger=logger)  
def getUniqueFieldValues(featureClass, fieldName, where=None, getValueFunction=None):
	'''
	Returns list of unique values for fieldName
	'''
	unique_values = []
	seen = set()
	with arcpy.da.SearchCursor(featureClass, [fieldName], where) as cursor:
		for r in cursor:
			val = getValueFunction and getValueFunction(r) or r[0]
			seen.add(val)
	return list(seen)


def getDuplicateFieldValues(featureClass, fieldName, where=None, getValueFunction=None):
	'''
	Returns list of duplicate values for fieldName
	'''
	duplicate_values = []
	seen = set()
	with arcpy.da.SearchCursor(featureClass, [fieldName], where) as cursor:
		for r in cursor:
			val = getValueFunction and getValueFunction(r) or r[0]
			if val in seen:
				duplicate_values.append(val)
			else:
				seen.add(val)
	return duplicate_values

@standardErrorLoggging(logger=logger)
def intToWord(n):
	ones = ["", "one ","two ","three ","four ", "five ",
			"six ","seven ","eight ","nine "]
	
	tens = ["ten ","eleven ","twelve ","thirteen ", "fourteen ",
			"fifteen ","sixteen ","seventeen ","eighteen ","nineteen "]
	
	twenties = ["","","twenty ","thirty ","forty ",
			"fifty ","sixty ","seventy ","eighty ","ninety "]
	
	thousands = ["","thousand ","million ", "billion ", "trillion ",
			"quadrillion ", "quintillion ", "sextillion ", "septillion ","octillion ",
			"nonillion ", "decillion ", "undecillion ", "duodecillion ", "tredecillion ",
			"quattuordecillion ", "sexdecillion ", "septendecillion ", "octodecillion ",
			"novemdecillion ", "vigintillion "]
	

	# break the number into groups of 3 digits using slicing
	# each group representing hundred, thousand, million, billion, ...
	n3 = []
	r1 = ""
	
	# create numeric string
	ns = str(n)
	for k in range(3, 33, 3):
		r = ns[-k:]
		q = len(ns) - k
	
		# break if end of ns has been reached
		if q < -2:
			break
		else:
			if q >= 0:
				n3.append(int(r[:3]))
			elif q >= -1:
				n3.append(int(r[:2]))
			elif q >= -2:
				n3.append(int(r[:1]))
		r1 = r
	#print n3 # test
	
	# break each group of 3 digits into
	# ones, tens/twenties, hundreds
	# and form a string
	nw = ""
	for i, x in enumerate(n3):
		b1 = x % 10
		b2 = (x % 100)//10
		b3 = (x % 1000)//100
		
		#print b1, b2, b3 # test
		if x == 0:
			continue # skip
		else:
			t = thousands[i]
		if b2 == 0:
			nw = ones[b1] + t + nw
		elif b2 == 1:
			nw = tens[b1] + t + nw
		elif b2 > 1:
			nw = twenties[b2] + ones[b1] + t + nw
		if b3 > 0:
			nw = ones[b3] + "hundred " + nw
			
	return nw


if __name__ == '__main__':
	pass