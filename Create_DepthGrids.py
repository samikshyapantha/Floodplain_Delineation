# ---------------------------------------------------------------------------
# DepthGrids_scripttool.py
#Revised on 5/20/2025
#-----------------------------------------------------------------------
import os
import time
import datetime
import arcpy
import gc
from arcpy.sa import Minus, Con
print('Starting up at...', datetime.datetime.now())
startdtime = datetime.datetime.now()
# Check out Spatial Analyst
arcpy.CheckOutExtension('Spatial')
arcpy.env.overwriteOutput = True
# Script parameters
Folder      = arcpy.GetParameterAsText(0)
topo        = arcpy.GetParameterAsText(1)
WSEL10      = arcpy.GetParameterAsText(2)
WSEL04      = arcpy.GetParameterAsText(3)
WSEL02      = arcpy.GetParameterAsText(4)
WSEL01      = arcpy.GetParameterAsText(5)
WSEL0_2     = arcpy.GetParameterAsText(6)
WSEL01p     = arcpy.GetParameterAsText(7)
WSEL01m     = arcpy.GetParameterAsText(8)
logfilename = arcpy.GetParameterAsText(9)
# Feedback helper
def feedback(msg):
    arcpy.AddMessage(msg)
    print(msg)
    f.write(msg + os.linesep)
# Enable garbage collection
gc.enable()
# Start log file
dtime = datetime.datetime.now().strftime('%Y%m%d_%H%M')
txtfile = os.path.join(Folder, f'{logfilename}_{dtime}.txt')
f = open(txtfile, 'w')
f.write('Depth Grids Script Tool log' + os.linesep)
f.write('Script began at: ' + str(datetime.datetime.now()) + os.linesep)
feedback('=======================================================================')
# Build list of WSEL rasters
wsels = []
for tag, path in [
    ('_10pct',  WSEL10),
    ('_04pct',  WSEL04),
    ('_02pct',  WSEL02),
    ('_01pct',  WSEL01),
    ('_0_2pct', WSEL0_2),
    ('_01plus', WSEL01p),
    ('_01minus',WSEL01m)
]:
    if path:
        wsels.append((tag, path))
feedback(f'WSELs to run acquired: {wsels}')
# Report inputs
feedback('INPUTS:')
feedback(f'  Topo: {topo}')
r_topo = arcpy.Raster(topo)
feedback(f'    cellsize: {r_topo.meanCellWidth} {r_topo.spatialReference.linearUnitName}')
feedback('  WSEL GRIDS:')
for tag, path in wsels:
    r_w = arcpy.Raster(path)
    feedback(f'    {path}')
    feedback(f'      cellsize: {r_w.meanCellWidth} {r_w.spatialReference.linearUnitName}')
feedback('OUTPUTS:')
feedback(f'  Folder: {Folder}')
feedback(f'  Logfile: {logfilename}_{dtime}.txt')
# Set environments
arcpy.AddMessage('Topo spatial reference = ' + r_topo.spatialReference.name)
arcpy.env.outputCoordinateSystem = r_topo.spatialReference
csize = float(arcpy.GetRasterProperties_management(topo, 'CELLSIZEX').getOutput(0))
arcpy.AddMessage(f'Topo cellsize = {csize} {r_topo.spatialReference.linearUnitName}')
arcpy.env.snapRaster = r_topo
# Compute combined extent of all WSEL rasters
ext = arcpy.Extent()
for _, path in wsels:
    e = arcpy.Raster(path).extent
    ext.XMin = min(ext.XMin or e.XMin, e.XMin)
    ext.YMin = min(ext.YMin or e.YMin, e.YMin)
    ext.XMax = max(ext.XMax or e.XMax, e.XMax)
    ext.YMax = max(ext.YMax or e.YMax, e.YMax)
arcpy.env.extent = ext
# Create output geodatabase if needed
GDBnmDG = 'DepthGrids'
GDB_DG  = os.path.join(Folder, f'{GDBnmDG}.gdb')
if not arcpy.Exists(GDB_DG):
    arcpy.CreateFileGDB_management(Folder, GDBnmDG)
# Process each WSEL raster
for tag, origraster in wsels:
    gc.collect()
    rasnm = tag[1:]
    
    # 1) Subtract topo
    feedback(f'Minus {rasnm}...')
    outMinus = Minus(origraster, topo)
    rasMinus = os.path.join(GDB_DG, f'DepthWithNeg{tag}')
    outMinus.save(rasMinus)
    del outMinus
    
    # 2) Reload from disk to avoid pointer issues
    in_minus = arcpy.Raster(rasMinus)
    
    # 3) Zero‐out negatives via Con (with retry)
    rasFinal = os.path.join(GDB_DG, f'DepthRaw{tag}')
    feedback(f'Cleaning negatives via Con for {rasnm}...')
    for attempt in range(3):
        try:
            outRas = Con(in_minus >= 0, in_minus)
            #Ensure no old FGDB raster blocks the save
            if arcpy.Exists(rasFinal):
                arcpy.Delete_management(rasFinal)
            outRas.save(rasFinal)
            del outRas
            break
        except RuntimeError as e:
            arcpy.AddWarning(f' Con attempt {attempt+1} failed: {e}')
            time.sleep(1)
    else:
        raise RuntimeError(f'Con failed after 3 tries for {rasnm}')
    
    # 4) Build pyramids & calculate statistics
    feedback(f'Building pyramids & stats for {rasnm}...')
    arcpy.BuildPyramids_management(rasFinal)
    arcpy.CalculateStatistics_management(rasFinal)
    feedback(f'{rasnm} done')
# Finish log
feedback('=======================================================================')
f.write('Script ended at: ' + str(datetime.datetime.now()) + os.linesep)
runtime = datetime.datetime.now() - startdtime
feedback(f'Time taken: {runtime}')
f.close()
print('Done at', datetime.datetime.now())
