import os, json
import deepdiff # deepdiff
from django.test import TestCase

from geodata.geodata import GeoData

class ReaderTest(TestCase):
    def test_read_zipped_shapefile(self):
        print("Read and Interpret a zipped shapefile")

        # check that shapefile is available
        self.assertTrue(os.path.exists('/usr/local/apps/marineplanner-core/apps/madrona-gis/geodata/tests/data/'))
        file_name = 'small_polygon_treatment_4326'
        file_location = '/usr/local/apps/marineplanner-core/apps/madrona-gis/geodata/tests/data/%s.zip' % file_name
        self.assertTrue(os.path.isfile(file_location))

        # Hand Zipped shapefile to the reader
        geodata = GeoData()
        geodata.read(file_location, "zip", 4326)

        # Query Projection
        self.assertEqual(geodata.getProjectionStr(), 'EPSG:4326')
        self.assertEqual(geodata.getProjectionAsProj4(), '+proj=longlat +datum=WGS84 +no_defs +type=crs')
        self.assertEqual(geodata.getProjectionID(), 4326)

        # Query Feature Count
        self.assertEqual(geodata.getFeatureCount(), 1)

        # Query Feature type(s)
        self.assertEqual(geodata.getFeatureTypes(), ['Polygon'])

        # Query Bbox
        self.assertEqual(
            geodata.getBbox(),
            'POLYGON ((-120.4947423934936523 48.3560494093161850, -120.4852581024169780 48.3560494093161850, -120.4852581024169780 48.3669133157431546, -120.4947423934936523 48.3669133157431546, -120.4947423934936523 48.3560494093161850))'
        )

        # Check GeoJSON
        geojson = json.loads(geodata.getGeoJSON())
        json_file = open("/usr/local/apps/marineplanner-core/apps/madrona-gis/geodata/tests/data/small_polygon_treatment_4326.geo.json")
        file_dict = json.loads(json_file.read())
        json_file.close()
        diff = deepdiff.DeepDiff(geojson, file_dict, ignore_order=True) # json writer may not return coords in same order
        self.assertEqual(diff, {})

        # Check TopoJSON
        topojson = json.loads(geodata.getTopoJSON())
        json_file = open("/usr/local/apps/marineplanner-core/apps/madrona-gis/geodata/tests/data/small_polygon_treatment_4326.topo.json")
        file_dict = json.loads(json_file.read())
        json_file.close()
        diff = deepdiff.DeepDiff(topojson, file_dict, ignore_order=True) # json writer may not return coords in same order
        self.assertEqual(diff, {})

        # Check WKT
        intended_WKT = 'GEOMETRYCOLLECTION (POLYGON ((-120.4947423934936523 48.3656588097173952, -120.4916524887084961 48.3669133157431546, -120.4862880706787109 48.3666852260368998, -120.4852581024169780 48.3581311246341912, -120.4904508590698100 48.3562490295407343, -120.4942703247070312 48.3560494093161850, -120.4947423934936523 48.3656588097173952)))'
        self.assertEqual(geodata.getWKT(), intended_WKT)

        # Check KML
        kml_str = geodata.getKML()
        kml_file = open("/usr/local/apps/marineplanner-core/apps/madrona-gis/geodata/tests/data/small_polygon_treatment_4326.kml")
        file_str = kml_file.read()
        kml_file.close()
        tmp_name_index = kml_str.index("<Schema name=\"") + 14
        tmp_name_length = 11
        tmp_name = kml_str[tmp_name_index:tmp_name_index+tmp_name_length]
        test_tmp_name = 'tmpfozk74un'
        self.assertEqual(file_str, kml_str.replace(tmp_name, test_tmp_name))

        # Check SQL
        sql_str = geodata.getPGSQL()
        sql_file = open("/usr/local/apps/marineplanner-core/apps/madrona-gis/geodata/tests/data/small_polygon_treatment_4326.sql")
        file_str = sql_file.read()
        sql_file.close()
        tmp_name_index = sql_str.index("DROP TABLE IF EXISTS \"public\".\"") + 31
        tmp_name_length = 11
        tmp_name = sql_str[tmp_name_index:tmp_name_index+tmp_name_length]
        test_tmp_name = 'small_polygon_treatment_4326'
        self.assertEqual(file_str, sql_str.replace(tmp_name, test_tmp_name))

        # Check .SHP
        # TODO: How?

        # Check reprojected GeoJSON
        geojson = json.loads(geodata.getGeoJSON("EPSG:3857"))
        json_file = open("/usr/local/apps/marineplanner-core/apps/madrona-gis/geodata/tests/data/small_polygon_treatment_3857.geo.json")
        file_dict = json.loads(json_file.read())
        json_file.close()
        diff = deepdiff.DeepDiff(geojson, file_dict, ignore_order=True) # json writer may not return coords in same order
        self.assertEqual(diff, {})

        # Check reprojected WKT
        intended_WKT = 'GEOMETRYCOLLECTION (POLYGON ((-120.4947423934936523 48.3656588097173952, -120.4916524887084961 48.3669133157431546, -120.4862880706787109 48.3666852260368998, -120.4852581024169780 48.3581311246341912, -120.4904508590698100 48.3562490295407343, -120.4942703247070312 48.3560494093161850, -120.4947423934936523 48.3656588097173952)))'
        # Okay, so reprojecting from 4326 to 4326, but still worth testing!
        self.assertEqual(geodata.getWKT(projection="EPSG:4326"), intended_WKT)
