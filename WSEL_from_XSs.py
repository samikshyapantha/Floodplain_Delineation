# ---------------------------------------------------------------------------
# WSELfromXS_scripttool.py
# Created in October 2010
# by Z. Zaloudek
#Revised by Samikshya Pantha 5/20/2025
# REQUIREMENTS:
#  1) XS must be in a personal or file geodatabase.
#  2) The stream name field must exist in XS and clipper with the same name.
#  3) Stream names in the stream name fields must match.
# ---------------------------------------------------------------------------

import os, datetime, arcpy, gc
from arcpy.sa import *

print('Starting up at...')
print(datetime.datetime.today())
startdtime = datetime.datetime.today()

# Check out any necessary licenses
arcpy.CheckOutExtension('3D')
arcpy.CheckOutExtension('spatial')

# ArcPy environment settings
arcpy.env.overwriteOutput = True

# Script Parameters
Folder = arcpy.GetParameterAsText(0)
topo = arcpy.GetParameterAsText(1)
XS = arcpy.GetParameterAsText(2)
WTR_NM_field = arcpy.GetParameterAsText(3)
clipper = arcpy.GetParameterAsText(4)
WSEL10field = arcpy.GetParameterAsText(5)
WSEL04field = arcpy.GetParameterAsText(6)
WSEL02field = arcpy.GetParameterAsText(7)
WSEL01field = arcpy.GetParameterAsText(8)
WSEL0_2field = arcpy.GetParameterAsText(9)
WSEL01pfield = arcpy.GetParameterAsText(10)
WSEL01mfield = arcpy.GetParameterAsText(11)
logfilename = arcpy.GetParameterAsText(12)
runqc = arcpy.GetParameter(13)

# Feedback function for user messages
def feedback(msg):
    print(msg)
    arcpy.AddMessage(msg)
    f.write(msg + '\n')

# Other variables
wtrnmMaxLen = 48  # Max water name length

# Enable automatic garbage collection
gc.enable()

# Start a log text file to store inputs, outputs, and settings chosen by the user
dtime = (datetime.datetime.today()).strftime('%Y%m%d_%H%M')
txtfile = os.path.join(Folder, f'{logfilename}_{dtime}.txt')
f = open(txtfile, 'w')
f.write('WSEL from XS Script Tool log\n')
f.write('Script began at: ' + str(datetime.datetime.today()) + '\n')
feedback('=======================================================================')
feedback('SETTINGS:')
feedback('  Run QC:\n    ' + str(runqc))

# Make a list of WSELs to run
wsels = []
if WSEL10field != '':
    wsels.append(['W10', WSEL10field, 'WSE_10pct'])
if WSEL04field != '':
    wsels.append(['W04', WSEL04field, 'WSE_04pct'])
if WSEL02field != '':
    wsels.append(['W02', WSEL02field, 'WSE_02pct'])
if WSEL01field != '':
    wsels.append(['W01', WSEL01field, 'WSE_01pct'])
if WSEL0_2field != '':
    wsels.append(['W002', WSEL0_2field, 'WSE_0_2pct'])
if WSEL01pfield != '':
    wsels.append(['W01p', WSEL01pfield, 'WSE_01plus'])
if WSEL01mfield != '':
    wsels.append(['W01m', WSEL01mfield, 'WSE_01minus'])

arcpy.AddMessage('Inputs acquired:')
arcpy.AddMessage(wsels)
print('wsels', wsels)

feedback('INPUTS:')
feedback('  Topo:\n    ' + str(topo))
feedback('    cellsize: ' + str(arcpy.Raster(topo).meanCellWidth) + ' ' + arcpy.Describe(topo).spatialReference.linearUnitName)
feedback('  XS:\n    ' + str(XS))
feedback('    WTR_NM field: ' + str(WTR_NM_field))
feedback('  Clipper:\n    ' + str(clipper))
feedback('    WTR_NM field:  ' + str(WTR_NM_field))
feedback('  WSEL fields:')
for wsel in wsels:
    feedback('    ' + wsel[0] + ' field: ' + wsel[1])
feedback('OUTPUTS:')
feedback('  Folder:\n    ' + Folder)
feedback('  Logfile:\n    ' + logfilename + '_' + dtime + '.txt')

# Turn topo raster into raster object and get its properties
toporaster = arcpy.Raster(topo)
topoND = toporaster.noDataValue

# Spatial reference
SpatRef = toporaster.spatialReference
arcpy.AddMessage('Topo spatial reference = ' + SpatRef.name)
arcpy.env.outputCoordinateSystem = SpatRef
linunits = SpatRef.linearUnitName

# Cellsize
csize = arcpy.GetRasterProperties_management(toporaster, 'CELLSIZEX')
cellsize = 'CELLSIZE ' + str(csize)
arcpy.AddMessage('Topo cellsize = ' + cellsize + ' ' + linunits)

# Snap raster
arcpy.env.snapRaster = toporaster

# All water surface elevations are assumed to be in FEET!
if 'foot' in linunits or 'feet' in linunits:
    zfact = 1
elif 'meter' in linunits:
    zfact = 0.3048

# Create a buffer version of the polygons (to avoid 'holes in seams')
polybuff = clipper + '_Buff'
buffdist = (float(cellsize.split()[1])) * 0.75
arcpy.Buffer_analysis(clipper, polybuff, buffdist, 'OUTSIDE_ONLY', '', 'LIST', WTR_NM_field)
polymerge = clipper + '_Merge'
arcpy.Merge_management([clipper, polybuff], polymerge)
polybuffer = clipper + '_Buffer'
arcpy.Dissolve_management(polymerge, polybuffer, WTR_NM_field, '', 'SINGLE_PART')
arcpy.Delete_management(polybuff)
arcpy.Delete_management(polymerge)
arcpy.AddMessage('Clipper polygon(s) buffered by: ' + str(buffdist) + ' ' + linunits)

# Only set extent if the topo & clipper polygons have the same spatial reference name!
if SpatRef.name == arcpy.Describe(polybuffer).spatialReference.name:
    # Get the extent of all buffered clipper polygons (to reduce processing time)
    clipperext = arcpy.Extent()
    with arcpy.da.SearchCursor(polybuffer, ['SHAPE@']) as cursor:
        for row in cursor:
            geom = row[0]
            minx = geom.extent.XMin
            if minx < clipperext.XMin or clipperext.XMin == 0:
                clipperext.XMin = minx
            miny = geom.extent.YMin
            if miny < clipperext.YMin or clipperext.YMin == 0:
                clipperext.YMin = miny
            maxx = geom.extent.XMax
            if maxx > clipperext.XMax or clipperext.XMax == 0:
                clipperext.XMax = maxx
            maxy = geom.extent.YMax
            if maxy > clipperext.YMax or clipperext.YMax == 0:
                clipperext.YMax = maxy
    del cursor
    print('Output Extent:', clipperext)
    arcpy.env.extent = clipperext
else:
    print('Topo has different spatial reference from clipper, not setting extent.')

# Create folder for individual stream data if it does not exist
streamsfolder = os.path.join(Folder, 'streams')
if not os.path.exists(streamsfolder):
    arcpy.CreateFolder_management(Folder, 'streams')

# Get all unique stream names
streams = []
with arcpy.da.SearchCursor(XS, WTR_NM_field) as cursor:
    for row in cursor:
        if row[0] not in streams:
            streams.append(row[0])
del cursor

# Edit stream names - remove certain characters and ensure max length
stmnew_list = []
charlist = [' ', '.', ',', '/', '-', '(', ')']
for stm in streams:
    if stm is not None:
        stmchop = stm
        for c in charlist:
            stmchop = stmchop.replace(c, '')
        if len(stmchop) > wtrnmMaxLen:
            stmchop = stmchop[:wtrnmMaxLen]
        stmnew_list.append(stmchop)

# Make master list of all stream names with short versions
allstreams = []
i = 0
for stream in streams:
    if stream and stream is not None:
        stmnm = stmnew_list[i]
        allstreams.append([stream, stmnm])
        i += 1
arcpy.AddMessage('Stream names acquired:')
arcpy.AddMessage(allstreams)
print('allstreams', allstreams)

# Make individual TINs & WSEL rasters
for thisstream in allstreams:
    gc.collect()
    stream = thisstream[0]
    stmnm = thisstream[1]
    print(stmnm)

    # Create folder for stream if it does not exist
    streamfolder = os.path.join(streamsfolder, stmnm)
    if len(streamfolder) > 108:
        streamfolder = streamfolder[:108]
        if os.path.exists(streamfolder):
            arcpy.AddError('PROBLEM - stream folder path+name are too long and a folder with truncated name (108 characters) already exists.\n' + 'Shorten output folder path+name and/or stream names\n' + streamfolder)
            break
        else:
            arcpy.AddError('FYI - stream folder path+name are long. Truncated to 108 characters.\n' + streamfolder)
    if not os.path.exists(streamfolder):
        arcpy.CreateFolder_management(streamsfolder, stmnm)

    # Create GDB for stream data if it does not exist
    GDB = os.path.join(streamfolder, f'{stmnm}.gdb')
    if not os.path.exists(GDB):
        arcpy.CreateFileGDB_management(streamfolder, stmnm)

    # Create a selection of buffered clipper for this stream
    wclause = f"{arcpy.AddFieldDelimiters(XS, WTR_NM_field)} = '{stream}'"
    thisClip = os.path.join(GDB, f'clipper_{stmnm}')
    arcpy.Select_analysis(polybuffer, thisClip, wclause)

    for wsel in wsels:
        gc.collect()
        wselnm = wsel[0]
        wselfield = wsel[1]
        print('', wselnm)

        # Create a selection of XS for this stream
        wclause = f"{arcpy.AddFieldDelimiters(XS, WTR_NM_field)} = '{stream}' AND {arcpy.AddFieldDelimiters(XS, wselfield)} >= 0 AND {arcpy.AddFieldDelimiters(XS, wselfield)} IS NOT NULL"
        theseXS = os.path.join(GDB, f'xs_{wselnm}')
        arcpy.Select_analysis(XS, theseXS, wclause)

        if int((arcpy.GetCount_management(theseXS)).getOutput(0)) > 0:
            try:
                # Create TIN
                WSEL_TIN = os.path.join(streamfolder, wselnm)
                arcpy.CreateTin_3d(WSEL_TIN, SpatRef)
                # Edit TIN
                edittinXS = f'"{theseXS}" {wselfield} <None> hardline false'
                edittinPOLY = f'"{thisClip}" <None> <None> hardclip false'
                edittin = f'{edittinXS}; {edittinPOLY}'
                arcpy.EditTin_3d(WSEL_TIN, edittin)
                # TIN to Raster
                WSEL_Raster = os.path.join(GDB, wselnm)
                arcpy.TinRaster_3d(WSEL_TIN, WSEL_Raster, 'FLOAT', 'LINEAR', cellsize, '1')
                arcpy.AddMessage(f' {stream} {wselnm} WSEL raster done')
                print(f' {stream} {wselnm} WSEL raster done')
            except Exception as e:
                arcpy.AddError(f'...ERROR, {stream} {wselnm} did not work')
                arcpy.AddMessage(str(e))
                print(f'...ERROR, {stream} {wselnm} did not work')
                print(str(e))
        else:
            arcpy.AddMessage(f'NO XS on {stream} for {wselnm}')
    i += 1
arcpy.AddMessage('Individual stream TINs/Rasters done')
print('Individual stream TINs/Rasters done')

# Now, mosaic all the individual stream rasters into one for each WSEL
GDBnm = 'WSELGrids_Mosaic'
GDB = os.path.join(Folder, f'{GDBnm}.gdb')
if not os.path.exists(GDB):
    arcpy.CreateFileGDB_management(Folder, GDBnm)

print('Number of unique stream names:', len(allstreams))
for wsel in wsels:
    gc.collect()
    indwselnm = wsel[0]
    wselnm = wsel[2]

    # Calculate input for mosaic tool
    wselraster_input = []
    for thisstream in allstreams:
        stmnm = thisstream[1]
        WSEL_Ras_clip = os.path.join(streamsfolder, stmnm, f'{stmnm}.gdb', indwselnm)
        if arcpy.Exists(WSEL_Ras_clip):
            wselraster_input.append(WSEL_Ras_clip)
    
    if wselraster_input:
        wselraster_input_str = ';'.join(wselraster_input)
        arcpy.AddMessage(f'Beginning mosaic for {wselnm}...')
        try:
            arcpy.MosaicToNewRaster_management(wselraster_input_str, GDB, wselnm, SpatRef, '32_BIT_FLOAT', csize, 1, 'BLEND')
            print(f'{wselnm} grids mosaicked')
            arcpy.AddMessage(f'{wselnm} grids mosaicked')
        except Exception as e:
            arcpy.AddError(f'...ERROR, {wselnm} mosaic failed')
            arcpy.AddMessage(str(e))
            print(f'...ERROR, {wselnm} mosaic failed')
            print(str(e))
    else:
        arcpy.AddMessage(f'No rasters found for mosaic for {wselnm}')
                                 
# Clean up and close the log file
feedback('=======================================================================')
f.write('Script ended at: ' + str(datetime.datetime.today()) + '\n')
enddtime = datetime.datetime.today()
runtime = enddtime - startdtime
feedback('Time taken: ' + str(runtime))
f.close()

print('Done at', datetime.datetime.today())
