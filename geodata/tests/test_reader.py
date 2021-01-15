import os
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
        print("TODO: Check GeoJSON - compare string against existing file format, or save as file and compare checksum")

        # Check TopoJSON
        print("TODO: Check TopoJSON - compare string against existing file format, or save as file and compare checksum")

        # Check WKT
        print("TODO: Check WKT")

        # Check KML
        print("TODO: Check KML - compare string against existing file format, or save as file and compare checksum")

        # Check SQL
        print("TODO: Check SQL - compare string against existing file format, or save as file and compare checksum")

        # Check reprojected WKT
        print("TODO: Check reprojected WKT")
