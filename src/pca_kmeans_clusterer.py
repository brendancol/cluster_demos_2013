import arcpy
import numpy
import time

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.cluster.DBSCAN

def main():
	try:
		feature_class = r'C:\gis_working_directory\school_clustering.gdb\CCD_10_11'
		data = arcpy.da.FeatureClassToNumPyArray(feature_class, ["OID@", "SHAPE@X", "SHAPE@Y"], skip_nulls=True)
		st = time.time()

		data = data.astype([('OID@', 'Float64'), ('SHAPE@X', 'Float64'), ('SHAPE@Y', 'Float64')])
		data_view = data.view((data.dtype[0], len(data.dtype.names)))
		scaler = StandardScaler()
		points = data_view[:,1:]
		points = scaler.fit_transform(points)
		print points

		#pca = PCA()
		#pca.n_components = 50
		#pca = pca.fit(points)
		#print len(pca.components_)
		centroids, _ = KMeans(init='k-means++', n_clusters=50, n_init=1, precompute_distances=True).fit(points)
		print centroids
		print("Elapsed time: ", time.time() - st) 
	except Exception as e:
		print "CRAP ERROR ==> {}".format(e)
		raise

if __name__ == '__main__':
	main()