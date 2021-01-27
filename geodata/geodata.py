import os, io
from json import dumps, loads
from zipfile import ZipFile
import topojson as tp
import geopandas
from django.core.files.temp import NamedTemporaryFile
import fiona

##############################################################################
#       Class: GeoData
##############################################################################

#
# GeoData
# - Import various data formats and store data as a
#       geopandas.geodataframe.GeoDataFrame
# - Export data various formats using provided projection

class GeoData:
    def __init__(self):
        self.data = None

    def read(self, file_name, format=None, projection="EPSG:4326"):
        initial_format = getDataFormat(file_name, format)
        read_method_switcher = {
            'zip': readZipFile,
            # 'shp': readShapefile,
            # 'geojson': readGeoJSON
        }
        reader = read_method_switcher.get(initial_format, projection)
        self.data = reader(file_name, projection)

    def removeOverlap(self):
        for target_geom in self.data.geometry:
            if not target_geom.is_valid:
                target_geom = target_geom.buffer(0)
            if target_geom.is_valid:
                for difference_geom in self.data.geometry:
                    if not difference_geom.is_valid:
                        difference_geom = difference_geom.buffer(0)
                    if difference_geom.is_valid and not target_geom == difference_geom and target_geom.intersects(difference_geom) and target_geom.type == difference_geom.type:
                        target_geom = target_geom.difference(difference_geom)

    def getProjectionStr(self):
        return self.data.geometry.crs.to_string()

    def getProjectionAsProj4(self):
        return self.data.geometry.crs.to_proj4()

    def getProjectionID(self):
        return self.data.geometry.crs.to_epsg()

    def getFeatureCount(self):
        return self.data.geometry.count()

    def getFeatureTypes(self):
        return self.data.geometry.type.to_list()

    def getBbox(self, projection="EPSG:4326"):
        envelope = self.data.to_crs(projection).geometry.envelope.to_list()[0]
        return envelope.to_wkt()

    def getGeoJSON(self, data=None, projection="EPSG:4326"):
        if not type(data) == geopandas.geodataframe.GeoDataFrame:
            data = self.data
        return data.to_crs(projection).to_json()

    def getTopoJSON(self, projection="EPSG:4326", enforce_topo=False):
        return tp.Topology(loads(self.getGeoJSON(projection))['features'], prequantize=False, topology=enforce_topo).to_json()

    def getWKT(self, data=None, projection="EPSG:4326"):
        if not type(data) == geopandas.geodataframe.GeoDataFrame:
            data = self.data
        geometries = [geom.to_wkt() for geom in data.to_crs(projection).geometry.to_list()]
        return "GEOMETRYCOLLECTION (%s)" % ", ".join(geometries)

    def getKML(self, projection="EPSG:4326"):
        fiona.supported_drivers['KML'] = 'rw'
        tmp_kml_file = NamedTemporaryFile(mode='w+',delete=True)
        self.data.to_crs(projection).to_file(tmp_kml_file.name, driver='KML')
        kml_str = tmp_kml_file.file.read()
        tmp_kml_file.close()
        return kml_str

    # getPGSQL:
    # - Get a string of a SQL script to import your data into a PostGIS DB
    # TODO: allow method to accept DB name, table name, whether/not to delete table
    def getPGSQL(self, projection="EPSG:4326"):
        # Create temporary named file of GeoJSON output
        tmp_json_file = NamedTemporaryFile(mode='w+',delete=True, suffix='.geo.json')
        tmp_json_file.write(self.getGeoJSON(projection))
        tmp_json_file.seek(0)
        # Create temporary named file for new pgsql output
        # we're using NamedTemporaryFile to create the unique filename...
        tmp_sql_file = NamedTemporaryFile(mode='w+',delete=True, suffix='.sql')
        tmp_sql_file_name = tmp_sql_file.name
        tmp_sql_file.close()
        # ... But we let ogr2ogr actually create the file and manually delete later.

        # call ogr2ogr to populate .sql file
        os.system('ogr2ogr -f "PGDUMP" %s %s -lco SRID=4326 -lco SCHEMA=public -lco EXTRACT_SCHEMA_FROM_LAYER_NAME="NO"' % (tmp_sql_file_name, tmp_json_file.name))
        # get sql string from .sql file
        tmp_sql_file = open(tmp_sql_file_name)
        sql_str = tmp_sql_file.read()
        # close all temporary files
        tmp_json_file.close()
        # tmp_sql_file.close()
        os.remove(tmp_sql_file_name)
        # return sql string.
        return sql_str

    def getSHP(self, projection="EPSG:4326"):
        # foo
        print("TODO: Wriet getSHP")

    def getUnion(self, format='gdf', projection="EPSG:4326"):
        union = self.data.unary_union
        uniongs = geopandas.GeoSeries(union)
        uniongdf = geopandas.GeoDataFrame(geometry=uniongs)
        # set CRS
        uniongdf.crs = self.data.crs
        if format == 'geojson':
            return self.getGeoJSON(data=uniongdf, projection=projection)
        if format == 'wkt':
            return self.getWKT(data=uniongdf, projection=projection)
        else:
            # TODO: support remaining formats as well, see "data" argument to override self.data
            return uniongdf



##############################################################################
#       Helper Functions
##############################################################################

def getDataFormat(file_name, format):
    # .shp (filename is a list where one file extension (lower) is ".shp")
    # .json (Topo or geo?)
    # .kml
    # WKT (string)
    # .SQL (pgsql vs mysql vs spatialite?)
    # Rasters?
    derived_format = "unknown"

    if format == None and file_name[-3:].lower() == "zip" or format and format.lower() == "zip":
        # TODO: sort out zip, gzip, bzip, tar, tar.gz, etc...
        if not file_name[-4:].lower() == ".zip":
            raise NotImplementedError("At this time, only zipped files of the '.zip' format are accepted")
        else:
            derived_format = "zip"

    if format != None and derived_format != format.lower() and derived_format != "unknown":
        # if we always use derived, then why do we even ask for format? Will there ever be ambiguity that it can resolve?
        print("WARNING: derived format '%s' does not match provided format '%s'! Using derived." % (derived_format, format))

    if derived_format != "unknown":
        return derived_format
    else:
        try:
            return format.lower()
        except AttributeError as e:
            # format is likely None
            return format
        except Exception as e:
            print("Unknown error occurred: %s" % e)
            return format

##############################################################################
#       Helper Functions: shapefiles (array or zip)
##############################################################################
def readZipFile(file_name, projection="EPSG:4326"):
        gdf = geopandas.read_file("zip://%s" % file_name)
        if not gdf.crs:
            print("Data CRS undetected: assuming %s" % projection)
            gdf.set_crs(projection)
        if not gdf.crs.equals(projection):
            print("Data source CRS [%s] does not match provided CRS. Reprojecting to %s" % (gdf.crs.to_string(), projection))
            gdf = gdf.to_crs(projection)
        return gdf
