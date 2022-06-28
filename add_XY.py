#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:     intern
#
# Author:      rnicolescu
#
# Created:     20/06/2022
# Copyright:   (c) rnicolescu 2022
# Licence:     <your license here>
#-------------------------------------------------------------------------------

from arcpy import env
from arcpy import *
import arcpy
import os
import glob
import time
import shutil

path_in = raw_input("Add the path from the shapefile:")
print "---> Processing path"
if path_in.endswith("\\"):
    path_in = path_in[0:-1]

main_source = os.path.join(*path_in.split("\\")[0:-1]).replace(":", ":\\") + "\\date_output"
temp_source = os.path.join(*path_in.split("\\")[0:-1]).replace(":", ":\\") + "\\temp_output"


if not os.path.exists(main_source):
    os.makedirs(main_source)
if not os.path.exists(temp_source):
    os.makedirs(temp_source)

def add_XY():
    env.workspace = path_in
    env.overwriteOutput = True

    print "---> Processing POINT shapefiles"
    for file in glob.glob(path_in + "\\*.shp"):
        fn = os.path.basename(file)
        if fn.endswith("_P.shp"):
            print "-------Processing {}".format(fn)
            arcpy.Copy_management(in_data=fn, out_data=main_source + "\\{}".format(fn))
            arcpy.AddXY_management(fn)
        if fn.endswith("_C.shp") or fn.endswith("_S.shp"):
            arcpy.Copy_management(in_data=fn, out_data=temp_source + "\\__{}".format(fn))

    print "---> Converting LINE | POLYGON features to POINT for adding coordinates"
    for file in glob.glob(path_in + "\\*.shp"):
        fn = os.path.basename(file)
        if fn.endswith("_C.shp") or fn.endswith("_S.shp"):
            arcpy.FeatureToPoint_management(fn, os.path.join(temp_source + "\\{}".format(fn)), "INSIDE")
            arcpy.AddXY_management(os.path.join(temp_source + "\\{}".format(fn)))
            arcpy.AddField_management(fn, "POINT_X", "TEXT", 80)
            arcpy.AddField_management(fn, "POINT_Y", "TEXT", 80)

    env.workspace = temp_source
    env.overwriteOutput = True

    for name in glob.glob(temp_source + "\\*.shp"):
        fn = os.path.basename(name)
        if fn.startswith("__"):
            arcpy.SpatialJoin_analysis(fn, fn[2:], temp_source + "\\temp_{}.shp".format(fn[2:]), join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_ALL", match_option="INTERSECT")
    for name in glob.glob(temp_source + "\\*.shp"):
        temp_fn = os.path.basename(name)
        if temp_fn.startswith("temp_"):
            print "-------- Processing {}".format(temp_fn)
            arcpy.CalculateField_management(temp_fn, "POINT_X", "!POINT_X_1!", "PYTHON_9.3")
            arcpy.CalculateField_management(temp_fn, "POINT_Y", "!POINT_Y_1!", "PYTHON_9.3")

    print "---> Deleting temp fields..."
    fcs = arcpy.ListFeatureClasses()
    features = {}
    csv_dict = {}
    for fc in fcs:
        cursor = arcpy.da.SearchCursor(fc, "*")
        if fc.startswith("__"):
            features[fc] = list(cursor.fields)
        if fc.startswith("temp_"):
            csv_dict[fc] = list(cursor.fields)

    for key, vals in features.items():
        for key2, val2 in csv_dict.items():
            for v in val2:
                if key[2:] == key2[5:]:
                    if not v in vals:
                        arcpy.DeleteField_management(key2, v)

    for name in glob.glob(temp_source + "\\*.shp"):
        temp_fn = os.path.basename(name)
        if temp_fn.startswith("temp_"):
            print "-------- Processing {}".format(temp_fn)
            arcpy.Copy_management(in_data=temp_fn, out_data=main_source + "\\{}".format(temp_fn[5:]))

def date_field():

    env.workspace = main_source
    env.overwriteOutput = True

    for file in glob.glob(main_source + "\\*.shp"):
        fn = os.path.basename(file)
        arcpy.AddField_management(in_table=fn, field_name="Date", field_type="TEXT", field_length=80)
        expression = "!Date!.replace(!Date!,'" + str(time.strftime("%d/%m/%Y")) + "')"
        arcpy.CalculateField_management(file, 'Date', expression, 'PYTHON_9.3')

if __name__ == '__main__':
    add_XY()
    date_field()

    shutil.rmtree(temp_source)



