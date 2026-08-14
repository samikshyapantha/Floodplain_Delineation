# ---------------------------------------------------------------------------
# Floodplains_scripttool.py
# Created in June 2011 by Z. Zaloudek
# Revised through May 28 2025 for ArcGIS Pro (Python 3.x)

# ---------------------------------------------------------------------------

import sys
import datetime
import arcpy
import gc

print("Starting up at...")
champmodulesfolder = r'\\Swsatlas\\champ\\Library\\software_utilities\\Grids_ScriptTools\\Scripts\\modules'
sys.path.append(champmodulesfolder)
import Templates, MiscOther
print(datetime.datetime.today())
startdtime = datetime.datetime.today()

from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')
arcpy.CheckOutExtension('3D')
arcpy.env.overwriteOutput = True

# Script Parameters
Folder = arcpy.GetParameterAsText(0)
WTR_LN = arcpy.GetParameterAsText(1)
OvTops = arcpy.GetParameterAsText(2)
DG10 = arcpy.GetParameterAsText(3)
DG04 = arcpy.GetParameterAsText(4)
DG02 = arcpy.GetParameterAsText(5)
DG01 = arcpy.GetParameterAsText(6)
DG0_2 = arcpy.GetParameterAsText(7)
DG01p = arcpy.GetParameterAsText(8)
DG01m = arcpy.GetParameterAsText(9)
minsqft = arcpy.GetParameter(10)
mindepth = arcpy.GetParameter(11)
cleanupmethod = arcpy.GetParameterAsText(12)
sorttype = arcpy.GetParameterAsText(13)
numruns = arcpy.GetParameterAsText(14)
algorithm = arcpy.GetParameterAsText(15)
tolerance = arcpy.GetParameter(16)
logfilename = arcpy.GetParameterAsText(17)
snstvty_TF = arcpy.GetParameter(18)

# Non-parameter variables
outGDBnm = 'Floodplains'
fldnm = ''
remwtrTF = False
if WTR_LN != '' and WTR_LN is not None:
    remwtrTF = True

# Feedback function
def feedback(msg):
    print(msg)
    arcpy.AddMessage(msg)
    f.write(msg + '\n')

# Enable automatic garbage collection
gc.enable()

# Dictionary of events & field names
evtflds = {
    '_10pct': 'WSEL_10',
    '_04pct': 'WSEL_25',
    '_02pct': 'WSEL_50',
    '_01pct': 'WSEL_100',
    '_0_2pct': 'WSEL_500',
    '_01plus': 'WSEL_100P',
    '_01minus': 'WSEL_100M',
}

# Create output geodatabases if needed

# Create (and clean up old) output geodatabases
outGDB = f"{Folder}\\{outGDBnm}.gdb"
if arcpy.Exists(outGDB):
    arcpy.Delete_management(outGDB)
arcpy.CreateFileGDB_management(Folder, outGDBnm)

if snstvty_TF:
    saGDB = f"{Folder}\\{outGDBnm}_sensitivity.gdb"
    if arcpy.Exists(saGDB):
        arcpy.Delete_management(saGDB)
    arcpy.CreateFileGDB_management(Folder, f"{outGDBnm}_sensitivity")


# Log file
logpath = f"{Folder}\\{logfilename}_{datetime.datetime.today().strftime('%Y%m%d_%H%M')}.txt"
f = open(logpath, 'w')
f.write('Floodplains Script Tool log\n')
f.write('script began at: ' + str(datetime.datetime.today()) + '\n')

feedback('=' * 71)
feedback('SETTINGS:')
feedback(f'  Minimum area to keep polygons:\n    {minsqft} sq ft')
feedback(f'  Minimum depth to consider flooded:\n    {mindepth} ft')
feedback(f'  Cleanup Method:\n    {cleanupmethod}')
if cleanupmethod == 'Boundary Clean':
    feedback(f'      Sort Type:  {sorttype}')
    feedback(f'      Number Runs:  {numruns}')
elif cleanupmethod == 'Contour':
    feedback(f'      Simplification Algorithm:  {algorithm}')
    feedback(f'      Simplification Tolerance:  {tolerance}')
feedback(f'  Run Sensitivity Analysis:\n    {snstvty_TF}')
feedback(f'  Remove polygons not intersecting water lines:\n    {remwtrTF}')

feedback('INPUT FEATURES:')
feedback(f'  Water Lines:\n    {WTR_LN}')
feedback(f'  Overtopping Polygons:\n    {OvTops}')

# List of rasters
dgrids = []
for name, val in zip(['_10pct','_04pct','_02pct','_01pct','_0_2pct','_01plus','_01minus'], [DG10, DG04, DG02, DG01, DG0_2, DG01p, DG01m]):
    if val and val != '':
        dgrids.append([name, val])

feedback('INPUT DEPTH GRIDS:')
for dgrid in dgrids:
    raster = arcpy.Raster(dgrid[1])
    cellsize = raster.meanCellWidth
    unit = arcpy.Describe(raster).spatialReference.linearUnitName
    feedback(f'  {dgrid[1]}')
    feedback(f'    cellsize: {cellsize} {unit}')

feedback('OUTPUTS:')
feedback(f"  Folder:\n    {Folder}")
feedback(f"  Logfile:\n    {logfilename}_{datetime.datetime.today().strftime('%Y%m%d_%H%M')}.txt")

def makepolys(GDB, pctnm, origraster, minsqft, cleanupmethod, setting1, setting2, forSnstvtyAnalysis, Folder, mindepth, remwtrTF, WTR_LN):
    fldnm = 'gridcode'
    i = 1
    feedback(f"[makepolys] Processing {pctnm} - method: {cleanupmethod}")

    remap = RemapValue([[-1000, mindepth - 0.001, 1], [mindepth, 1000, 0]])
    outRas1 = Reclassify(origraster, 'VALUE', remap)
    rasRound1 = f"{GDB}\\FP{pctnm}_{i}"
    if not forSnstvtyAnalysis:
        outRas1.save(rasRound1)
    i += 1

    if cleanupmethod == 'Boundary Clean':
        outRas2 = BoundaryClean(outRas1, setting1, setting2)
    else:
        feedback('[makepolys] Contour method not implemented in this inline version.')
        return i

    rasRound2 = f"{GDB}\\FP{pctnm}_{i}"
    if not forSnstvtyAnalysis:
        outRas2.save(rasRound2)
    del outRas1
    i += 1

    # Convert raster to polygon
    FP_feat1 = f"{GDB}\\FP{pctnm}_{i}"
    arcpy.RasterToPolygon_conversion(outRas2, FP_feat1, 'SIMPLIFY')
    del outRas2
    i += 1



    # Calculate a one cell area threshold (you already have cellsize in your loop)
    cellsize = float(arcpy.Raster(origraster).meanCellWidth)
    area_thresh = cellsize * cellsize

    feedback(f" Eliminating interior holes smaller than {area_thresh:.2f}...")
    # temporary filled  polygon feature class
    filled_fc = f"{GDB}\\FP{pctnm}_{i}_filled"
    arcpy.EliminatePolygonPart_management(
        in_features=FP_feat1,
        out_feature_class=filled_fc,
        condition="AREA",
        part_area=str(area_thresh)
    )
    # Swap your working feature to the filled one
    FP_feat1 = filled_fc
    i += 1

    

    # Repair geometry
    arcpy.RepairGeometry_management(FP_feat1, 'DELETE_NULL')

    # Create removal feature class
    FP_removed = f"{GDB}\\FP{pctnm}_removed"
    arcpy.CreateFeatureclass_management(GDB, f"FP{pctnm}_removed", 'POLYGON', FP_feat1, '', '', FP_feat1)

    # Remove small polygons
    in_features = FP_feat1
    for _ in range(10):
        lyr = 'temp_lyr'
        arcpy.MakeFeatureLayer_management(in_features, lyr)
        wclause = arcpy.AddFieldDelimiters(lyr, 'Shape_Area') + f' < {minsqft}'
        arcpy.SelectLayerByAttribute_management(lyr, 'NEW_SELECTION', wclause)
        arcpy.Append_management(lyr, FP_removed, 'NO_TEST')
        out_fc = f"{GDB}\\FP{pctnm}_{i}"
        arcpy.Eliminate_management(lyr, out_fc, 'LENGTH')
        in_features = out_fc
        i += 1
        count = int(arcpy.GetCount_management(lyr).getOutput(0))
        if count == 0:
            break

    FP_feat2 = in_features

    # Remove polygons not touching water lines
    if remwtrTF and WTR_LN:
        WTRLN_lyr = 'water_ln'
        arcpy.MakeFeatureLayer_management(WTR_LN, WTRLN_lyr)
        feat_lyr = 'poly_ln'
        arcpy.MakeFeatureLayer_management(FP_feat2, feat_lyr)
        arcpy.SelectLayerByLocation_management(feat_lyr, 'INTERSECT', WTRLN_lyr, '', 'NEW_SELECTION')
        arcpy.SelectLayerByLocation_management(feat_lyr, 'INTERSECT', WTRLN_lyr, '', 'SWITCH_SELECTION')
        arcpy.Append_management(feat_lyr, FP_removed, 'NO_TEST')
        arcpy.SelectLayerByAttribute_management(feat_lyr, 'CLEAR_SELECTION')
        arcpy.SelectLayerByLocation_management(feat_lyr, 'INTERSECT', WTRLN_lyr, '', 'NEW_SELECTION')
        FP_feat3_nm = f"FP{pctnm}_{i}"
        i += 1
        FP_feat3 = f"{GDB}\\{FP_feat3_nm}"
        arcpy.FeatureClassToFeatureClass_conversion(feat_lyr, GDB, FP_feat3_nm)
    else:
        FP_feat3 = FP_feat2

    # Final filter only keep flooded polygons
    lyr = 'final_filter'
    arcpy.MakeFeatureLayer_management(FP_feat3, lyr)
    wclause = arcpy.AddFieldDelimiters(FP_feat3, fldnm) + ' = 0'
    FP_final = f"{GDB}\\FP{pctnm}"
    arcpy.Select_analysis(FP_feat3, FP_final, wclause)
    feedback(f"[makepolys] Final polygon count written to: {FP_final}")

    return i

# Loop through depth grids and call makepolys
feedback('=' * 71)
for dgrid in dgrids:
    gc.collect()
    pctnm, origraster = dgrid
    feedback(f"Working on {pctnm[1:]}...")

    depthraster = arcpy.Raster(origraster)
    arcpy.env.outputCoordinateSystem = depthraster.spatialReference
    arcpy.env.snapRaster = depthraster

    if cleanupmethod == 'Boundary Clean':
        i = makepolys(outGDB, pctnm, origraster, minsqft, cleanupmethod, sorttype, numruns, False, Folder, mindepth, remwtrTF, WTR_LN)
    elif cleanupmethod == 'Contour':
        i = makepolys(outGDB, pctnm, origraster, minsqft, cleanupmethod, algorithm, tolerance, False, Folder, mindepth, remwtrTF, WTR_LN)

    # Optional: Apply overtop fix (if applicable)
    if OvTops not in ('', None):
        feedback('Checking for overtopping polygons...')
        evtfld = evtflds.get(pctnm)

        if not evtfld:
            feedback(f"No overtopping field match found for {pctnm} in evtflds.")
        else:
            feedback(f"Looking for overtopping polygons with {evtfld} = 'Y' or 'y'")
            wclause = f"{arcpy.AddFieldDelimiters(OvTops, evtfld)} IN ('Y', 'y')"
            ovtflyr = f"OvTops{pctnm}"
            arcpy.MakeFeatureLayer_management(OvTops, ovtflyr, wclause)
            count = int(arcpy.GetCount_management(ovtflyr)[0])
            feedback(f"Found {count} overtopping polygons")

            if count > 0:
                FP_final = f"{outGDB}\\FP{pctnm}"
                oldFP_final = f"{outGDB}\\FP{pctnm}_{i}"
                i += 1
                arcpy.Rename_management(FP_final, oldFP_final)
                FPupdated = f"{outGDB}\\FP{pctnm}_{i}"
                i += 1
                arcpy.Update_analysis(oldFP_final, ovtflyr, FPupdated, 'BORDERS')
                arcpy.Dissolve_management(FPupdated, FP_final, 'gridcode', None, 'SINGLE_PART')
                feedback(f"Applied overtopping fix and created: {FP_final}")
            else:
                feedback("No overtopping polygons matched. Skipping overtopping fix.")


# Final log entries
feedback('=' * 71)
f.write('Script ended at: ' + str(datetime.datetime.today()) + '\n')
enddtime = datetime.datetime.today()
runtime = enddtime - startdtime
feedback(f'Time taken: {runtime}')
f.close()

print(' Done at', datetime.datetime.today())
