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
        self.assertEqual(geodata.getProjectionStr(), '+proj=longlat +datum=WGS84 +no_defs +type=crs')
        self.assertEqual(geodata.getProjectionID(), 4326)

        # Query Feature Count
        self.assertEqual(geodata.getFeatureCount(), 1)

        # Query Feature type(s)
        self.assertEqual(geodata.getFeatureType(), 'POLYGON')

        # Query Bbox
        self.assertEqual(str(geodata.getBbox()), str([
            -120.49474239349365,
            48.356049409316185,
            -120.48525810241698,
            48.366913315743155
        ]))

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
        intended_WKT = ['POLYGON ((-120.4947423934937 48.3656588097174, -120.4916524887085 48.36691331574315, -120.4862880706787 48.3666852260369, -120.485258102417 48.35813112463419, -120.4904508590698 48.35624902954073, -120.494270324707 48.35604940931619, -120.4947423934937 48.3656588097174))'
]
        self.assertEqual(geodata.getWKT(), intended_WKT)

        # Check KML
        print("TODO: Check KML - compare string against existing file format, or save as file and compare checksum")

        # Check SQL
        print("TODO: Check SQL - compare string against existing file format, or save as file and compare checksum")

        # Check reprojected WKT
        print("TODO: Check reprojected WKT")
