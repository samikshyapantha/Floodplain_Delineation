# Floodplain Mapping 

This repository contains three ArcGIS Pro Python script tools used to generate floodplain mapping data from HEC-RAS hydraulic modeling exports. The cross-section feature class contains water surface elevations (WSEL) values for different annual flood frequencies ( 10%, 25%, 50%, 100%, 500%, 100pc).

## Workflow

The scripts are designed to be run in this order: 
Cross Sections + streamlines + clipper polygon WSEL → WSEL Grids → Depth Grids → Floodplain Polygons**


# Floodplain Mapping Script Tools

Before running the script:

## Requirements

* ArcGIS Pro
* Python 3.x / ArcPy
* Spatial Analyst extension
* Appropriate input datasets and fields

* Cross-section data must be stored in a file geodatabase.
* The cross-section feature class and clipper polygon must contain the same stream name field.
* Stream names must match between the cross-section and clipper datasets.
.
## Scripts

### 1. WSELfromXS_scripttool.py

Creates Water Surface Elevation (WSEL) rasters from cross-section data.

**Inputs include:**

* Digital Elevation Model (DEM)
* Cross sections (XS)
* Stream name field
* Clipper polygons
* WSEL fields for different flood frequencies

The script creates individual WSEL TINs and rasters for each stream and mosaics them into WSEL grids. A file geodatabase named:
WSELGrids_Mosaic.gdb
is created in the output folder.

### 2. Create_DepthGrids.py

Creates depth grids by subtracting the topographic raster from the WSEL rasters.

Negative depth values are removed, and the resulting depth rasters are saved to a `DepthGrids.gdb`. Pyramids and statistics are also calculated for the output rasters.

### 3. Create_Floodplains.py

Converts depth grids into floodplain polygons.

The script:

* Reclassifies depth grids based on a minimum flood depth
* Cleans the resulting floodplain areas
* Converts rasters to polygons
* Removes small polygons and interior holes
* Optionally removes polygons that do not intersect water lines
* Applies overtopping polygons when provided
* Saves final floodplain polygons to `Floodplains.gdb`

## Outputs

The workflow produces:

* **WSELGrids_Mosaic.gdb** – WSEL rasters
* **DepthGrids.gdb** – depth rasters
* **Floodplains.gdb** – final floodplain polygon features
* Log files documenting script settings, inputs, and processing time
