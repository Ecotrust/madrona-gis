import io
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
#       geopandas.geodatafram.GeoDataFrame
# - Export data various formats using provided projection

class GeoData:
    def __init__(self):
        self.data = None

    def read(self, file_name, format=None, projection=None):
        initial_format = getDataFormat(file_name, format)
        read_method_switcher = {
            'zip': readZipFile,
            # 'shp': readShapefile,
            # 'geojson': readGeoJSON
        }
        reader = read_method_switcher.get(initial_format, projection)
        self.data = reader(file_name)

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

    def getBbox(self):
        envelope = self.data.geometry.envelope.to_list()[0]
        return envelope.to_wkt()

    def getGeoJSON(self):
        return self.data.to_json()

    def getTopoJSON(self):
        return tp.Topology(loads(self.getGeoJSON())['features'], prequantize=False).to_json()

    def getWKT(self):
        geometries = [geom.to_wkt() for geom in self.data.geometry.to_list()]
        return "GEOMETRYCOLLECTION (%s)" % ", ".join(geometries)

    def getKML(self):
        fiona.supported_drivers['KML'] = 'rw'
        tmp_kml_file = NamedTemporaryFile(mode='w+',delete=True)
        self.data.to_file(tmp_kml_file.name, driver='KML')
        kml_str = tmp_kml_file.file.read()
        tmp_kml_file.close()
        return kml_str


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

    if format.lower() == "zip" or format == None and file_name[-3:].lower() == "zip":
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
def readZipFile(file_name):
        gdf = geopandas.read_file("zip://%s" % file_name)
        return gdf
