# Floodplain Mapping 

This repository contains three Python script tools used to generate floodplain mapping data from HEC-RAS hydraulic modeling results in ArcGIS Pro. The scripts convert cross-section-based Water Surface Elevation (WSEL) information into WSEL rasters, depth rasters, and final floodplain polygons.

The scripts are designed to be used as part of a custom ArcGIS Pro toolbox. Users are recommended to create a customized toolbox, add the scripts as script tools, and configure the required inputs and parameters. 

## Workflow

The scripts are designed to be run in this order: 

Cross Sections + Streamlines  + Clipper Polygon + WSEL → WSEL Grids → Depth Grids → Floodplain Polygons
Each step uses the output from the previous step as an input.

## Requirements

* ArcGIS Pro
* Python 3.x / ArcPy
* Spatial Analyst extension in ArcPro


## Required Input Data

Before running the workflow, prepare the following datasets:

* Cross Sections
Must be stored in a file geodatabase.
Feature class must be named XSCutline.
Must contain the stream name field.
Must contain WSEL fields for the required flood frequencies.

*Streamlines
Must be stored in a file geodatabase.
Feature class must be named River2D.

* Clipper Polygon
Must be stored in a file geodatabase.
Feature class must be named Clipper.
Defines the spatial extent of the floodplain mapping.
Must contain the same stream name field as the cross-section feature class.

* Stream Names
Stream names must match between the cross-section and clipper datasets.

* DEM
A DEM representing the ground/topographic surface used for depth calculations


## Scripts

## 1. WSELfromXS_scripttool.py

Creates Water Surface Elevation (WSEL) rasters from cross-section data.

Inputs include:

Digital Elevation Model (DEM)
Cross-section feature class (XSCutline)
Stream name field
Streamline feature class (River2D)
Clipper polygons (Clipper)
WSEL fields for different flood frequencies

The script generates WSEL TINs and rasters for individual streams and combines them into WSEL grids.

Output:

WSELGrids_Mosaic.gdb – File geodatabase containing the resulting WSEL rasters.

## 2. Create_DepthGrids.py

Creates depth rasters by subtracting the DEM from the WSEL rasters.

The script:

Calculates flood depth from WSEL and ground elevation.
Removes negative depth values.
Calculates raster pyramids and statistics.
Saves the resulting depth rasters to a file geodatabase.

Output:

DepthGrids.gdb – File geodatabase containing the depth rasters.

## 3.  Create_Floodplains.py

Converts depth rasters into floodplain polygons.

The script:

Reclassifies depth rasters using a minimum flood-depth threshold.
Cleans the resulting floodplain areas.
Converts the raster results to polygons.
Removes small polygons and interior holes.
Optionally removes polygons that do not intersect streamlines.
Applies overtopping polygons when provided.

Overtopping polygons are used to force inundation in areas where the ground elevation is higher than the modeled WSEL but flooding is expected to occur due to overtopping.

Output:

Floodplains.gdb – File geodatabase containing the final floodplain polygon features.

## Outputs

The workflow produces:

* **WSELGrids_Mosaic.gdb** – WSEL rasters
* **DepthGrids.gdb** – depth rasters
* **Floodplains.gdb** – final floodplain polygon features

* Log files documenting script settings, inputs, and processing time
