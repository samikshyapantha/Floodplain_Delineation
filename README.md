# Delineation of Floodplains for FEMA RISK MAP Program

This repository contains three python scripts used to generate raster and vector based flood dataset from HEC-RAS hydraulic modeling results. These scripts convert cross-section-based Water Surface Elevation (WSE) information into WSE raster, depth grid raster, and final floodplain polygons. These scripts were designed specifically to meet the Federal Emergency Management Agency (FEMA) Risk Map Program technical standards for creating regulatory flood maps.

The scripts are designed to be used as part of custom ArcGIS Pro toolbox. Users are recommended to create a customized toolbox, add the scripts as script tools, and configure the required inputs and parameters. Each step uses the output from the previous step as an input.

## Workflow

The scripts are designed to be run in this order: 
Cross Sections + Streamlines  + Clipper Polygon + WSE → WSE Grids → Depth Grids → Floodplain Polygons

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

* Streamlines
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

Creates Water Surface Elevation Layer (WSEL) raster from cross-section data.
Inputs :

Digital Elevation Model (DEM)
Cross-section feature class (XSCutline)
Stream name field
Clipper polygons (Clipper)
WSEL fields for different flood frequencies

The script generates WSEL TINs and rasters for individual streams and combines them into WSEL grids.

Output:

WSELGrids_Mosaic.gdb – File geodatabase containing the resulting WSEL rasters.

## 2. Create_DepthGrids.py

Creates depth rasters by subtracting the DEM from the WSEL rasters.

It calculates flood depth from WSEL and ground elevation, removes negative depth values and calculates raster pyramids and statistics.
The resulting depth rasters are saved to a file geodatabase.
Input: 

Water Surface Elevation Layer created in the first step
Dgital Elevation Model(DEM)

Output:

DepthGrids.gdb – File geodatabase containing the depth rasters.

## 3.  Create_Floodplains.py

Converts depth rasters into floodplain polygons.

The script reclassifies depth rasters using a minimum flood-depth threshold,converts the raster results to polygons, removes any small polygons and interior holes 
Input:
Streamline feature class (River2D)
Depth Grids generated in the second step
Optional input: Overtopping polygons are used to force inundation in areas where the ground elevation is higher than the modeled WSEL but flooding is expected to occur.

Output:

Floodplains.gdb – File geodatabase containing the final floodplain polygon features.

## Outputs

The workflow produces:

* **WSELGrids_Mosaic.gdb** – WSEL rasters
* **DepthGrids.gdb** – depth rasters
* **Floodplains.gdb** – final floodplain polygon features

* Log files documenting script settings, inputs, and processing time
