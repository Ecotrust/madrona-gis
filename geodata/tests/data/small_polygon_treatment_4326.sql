SET standard_conforming_strings = OFF;
CREATE SCHEMA "public";
DROP TABLE IF EXISTS "public"."small_polygon_treatment_4326.geo" CASCADE;
DELETE FROM geometry_columns WHERE f_table_name = 'small_polygon_treatment_4326.geo' AND f_table_schema = 'public';
BEGIN;
CREATE TABLE "public"."small_polygon_treatment_4326.geo" ( "ogc_fid" SERIAL, CONSTRAINT "small_polygon_treatment_4326.geo_pk" PRIMARY KEY ("ogc_fid") );
SELECT AddGeometryColumn('public','small_polygon_treatment_4326.geo','wkb_geometry',4326,'POLYGON',2);
CREATE INDEX "small_polygon_treatment_4326.geo_wkb_geometry_geom_idx" ON "public"."small_polygon_treatment_4326.geo" USING GIST ("wkb_geometry");
ALTER TABLE "public"."small_polygon_treatment_4326.geo" ADD COLUMN "id" VARCHAR;
ALTER TABLE "public"."small_polygon_treatment_4326.geo" ADD COLUMN "fid" INTEGER;
INSERT INTO "public"."small_polygon_treatment_4326.geo" ("wkb_geometry" , "id", "fid") VALUES ('0103000020E61000000100000007000000000000DCA91F5EC0819D6AE8CD2E48400000003C771F5EC0B9CAF903F72E4840000000581F1F5EC09FE09E8AEF2E4840FFFFFF770E1F5EC0E5FD9D3DD72D4840FFFFFF8B631F5EC0FA8D7591992D484000000020A21F5EC0F662EC06932D4840000000DCA91F5EC0819D6AE8CD2E4840', '0', 0);
COMMIT;
