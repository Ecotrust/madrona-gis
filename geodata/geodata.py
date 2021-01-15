import shapefile    # pyshp
from pyproj import CRS
from osgeo import ogr
from zipfile import ZipFile

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
        # if prj_file_name:
        if shp_file_name:
            # projection = getShapefileProjection(prj_file_name, zipped=True, zip_source=zip)
            # https://gis.stackexchange.com/a/92838 -- Thanks to gene
            driver = ogr.GetDriverByName('ESRI Shapefile')
            ogr_data = driver.Open(shp_file_name)
            ogr_layer = ogr_data.GetLayer()
            projection = ogr_layer.GetSpatialRef().ExportToProj4()
        if shp_file_name and shx_file_name and dbf_file_name:
            shape_data = shapefile.Reader(
                shp=zipshape.open(shp_file_name),
                shx=zipshape.open(shx_file_name),
                dbf=zipshape.open(dbf_file_name),
            )

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
