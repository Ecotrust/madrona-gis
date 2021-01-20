import io
import shapefile    # pyshp
#import pygeoif      # pygeoif
from pyproj import CRS
from osgeo import ogr, osr
from json import dumps, loads
from zipfile import ZipFile
import topojson as tp
from shapely.geometry import shape as shapelyShape
# RDH 1/15/2021 -- pytopojson preserves more significant digits and topojson
# --- But to make it work I had to hack the source to insert an "items" key
# --- into the geojson. Until the below code works out of the box, use
# --- the python package "topojson"
# from pytopojson import topology

##############################################################################
#       Class: GeoData
##############################################################################

class GeoData:
    def __init__(self):
        self.data = None
        self.format = None  # 'zip', 'shp', 'geojson', 'wkt', 'topojson', 'kml', 'sql'
        self.crs = None  # Proj4 CRS

    def read(self, file_name, format=None, projection=None):
        self.format = getDataFormat(file_name, format)
        read_method_switcher = {
            'zip': readZipFile,
            # 'shp': readShapefile,
            # 'geojson': readGeoJSON
        }
        reader = read_method_switcher.get(self.format)
        reader_dict = reader(file_name, projection)
        self.data = reader_dict['data']
        self.format = reader_dict['format']
        self.crs = reader_dict['projection']

    def getProjectionStr(self):
        return self.crs.to_string()

    def getProjectionID(self):
        return self.crs.to_epsg()

    def getFeatureCount(self):
        count_method_switcher = {
            'shp': countShapefileFeatures,
            # 'shp': readShapefile,
            # 'geojson': readGeoJSON
        }
        counter = count_method_switcher.get(self.format)
        return counter(self.data)

    def getFeatureType(self):
        type_method_switcher = {
            'shp': getShapefileFeatureType,
        }

        type_finder = type_method_switcher.get(self.format)
        return type_finder(self.data)

    def getBbox(self):
        bbox_method_switcher = {
            'shp': getShapefileBbox,
        }
        bbox_getter = bbox_method_switcher.get(self.format)
        return bbox_getter(self.data)

    def getGeoJSON(self):
        getGeoJSON_method_switcher = {
            'shp': getShapefileAsGeoJSON,
        }
        geojson_getter = getGeoJSON_method_switcher.get(self.format)
        return geojson_getter(self.data)

    def getTopoJSON(self):
        getTopoJSON_method_switcher = {
            'shp': getShapefileAsTopoJSON,
        }
        topojson_getter = getTopoJSON_method_switcher.get(self.format)
        return topojson_getter(self.data)

    def getWKT(self):
        getWKT_method_switcher = {
            'shp': getShapefileAsWKT,
        }
        wkt_getter = getWKT_method_switcher.get(self.format)
        return wkt_getter(self.data)


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
def readZipFile(file_name, projection):
        # with ZipFile(file_name, 'r') as zipshape:
        zipshape = ZipFile(open(file_name, 'rb'))
        subfiles = zipshape.namelist()
        shp_file_name = shx_file_name = dbf_file_name = prj_file_name = False
        for subfile in subfiles:
            if subfile[-4:].lower() in ['.shp', '.shx', '.dbf', '.prj']:
                if subfile[-4:].lower() == '.shp':
                    shp_file_name = subfile
                if subfile[-4:].lower() == '.shx':
                    shx_file_name = subfile
                if subfile[-4:].lower() == '.dbf':
                    dbf_file_name = subfile
                if subfile[-4:].lower() == '.prj':
                    prj_file_name = subfile
        if prj_file_name:
            prj_file = zipshape.open(prj_file_name, 'r')
            prj_wkt_text = io.TextIOWrapper(prj_file).read()
            prj_file.close()
            srs = osr.SpatialReference()
            srs.ImportFromWkt(prj_wkt_text)
            projection = srs.ExportToProj4()
            if not "+type=crs" in projection:
                projection += " +type=crs"

        # elif shp_file_name:
        #     # this works great for unzipped shapefiles, but I can't figure out
        #     #       how to make driver.Open() work with a zipped shapefile
        #     #       Maybe I'll try with a tempfile approach:
        #     #       https://lists.osgeo.org/pipermail/gdal-dev/2007-July/013636.html
        #     # projection = getShapefileProjection(prj_file_name, zipped=True, zip_source=zip)
        #     # https://gis.stackexchange.com/a/92838 -- Thanks to gene
        #     driver = ogr.GetDriverByName('ESRI Shapefile')
        #     import ipdb; ipdb.set_trace()
        #     ogr_data = driver.Open(zipshape.open(shp_file_name))
        #     ogr_layer = ogr_data.GetLayer()
        #     projection = ogr_layer.GetSpatialRef().ExportToProj4()
        if shp_file_name and shx_file_name and dbf_file_name:
            shape_data = shapefile.Reader(
                shp=zipshape.open(shp_file_name),
                shx=zipshape.open(shx_file_name),
                dbf=zipshape.open(dbf_file_name),
            )

        # shape_data is a "shapefile.Reader" object - should we convert this to a GEOS Collection? How?
        #       GEOS Collection: bad - no attributes.
        #       GeoPandas may be a great option, though! (Better than shapefile.Reader object)

        return {
            'data': shape_data,
            'format': 'shp',        # we have read the data from the zip - zip no longer matters
            'projection': CRS.from_proj4(projection),
        }

def countShapefileFeatures(shape_data):
    shapes = shape_data.shapes()
    return len(shapes)

def getShapefileFeatureType(shape_data):
    return shape_data.shapeTypeName

def getShapefileBbox(shape_data):
    return shape_data.bbox

def getShapefileAsGeoJSON(shape_data):
    # Yanked straight from frankrowe at https://gist.github.com/frankrowe/6071443
    fields = shape_data.fields[1:]
    field_names = [field[0] for field in fields]
    buffer = []
    for sr in shape_data.shapeRecords():
       atr = dict(zip(field_names, sr.record))
       geom = sr.shape.__geo_interface__
       buffer.append(dict(type="Feature", geometry=geom, properties=atr))

    # generate the GeoJSON
    return dumps({"type": "FeatureCollection", "features": buffer}, indent=2)

def getShapefileAsTopoJSON(shape_data):
    geojson_data = getShapefileAsGeoJSON(shape_data)
    return tp.Topology(geojson_data, prequantize=False).to_json()
    # topology_ = topology.Topology()
    # return topology_(loads(geojson_data))

# def getShapefileAsGEOSCollection(shape_data):
#     geojson_data = loads(getShapefileAsGeoJSON(shape_data))

def getShapefileGeometriesAsShapely(shape_data):
    # Note: Shapely geometries do not maintain attributes!
    geojson_data = loads(getShapefileAsGeoJSON(shape_data))
    shapely_collection = []
    for feature in geojson_data['features']:
        shapely_collection.append(shapelyShape(feature['geometry']))
    return shapely_collection


def getShapefileAsWKT(shape_data):
    # NOTE: WKT data does not maintain attributes!

    # I started down this path:
    #       https://gis.stackexchange.com/questions/202662/export-geometry-to-wkt-using-pyshp#:~:text=Pyshp%20does%20not%20have%20a,module%20to%20convert%20to%20WKT.
    # However, it requires that you know the feature type (it assumes MultiPoint)

    return [shape.wkt for shape in getShapefileGeometriesAsShapely(shape_data)]
