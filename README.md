# PyWRF-Automation
Python automation script to download the Global Forecast System (GFS) data from NOMADS NOAA with spatial resolution 0.25<sup>0</sup> and execute Weather Research & Forecasting (WRF) model.

## Prerequisites
To using this script, you must complete following prerequisites such as:
1. Linux/Unix distribution
2. Python 3.7+
3. MPI Package (OpenMPI/Intel MPI/MPICH)
4. WRF-ARW Model with `em_real` case using `dmpar` compiler selection.

This repository includes two script, which is `main.py` as an executable script and `utils.py` as a collection of function that will be used by `main.py` script.

## How to use
1. Open `main.py` file and change the values from line 10 to 31:

```python
# Folder path
base_dir                = "/home/your_username/wrf_model"
gfs_dir                 = f"{base_dir}/gfs_dataset"         # Path to GFS dataset folder
wps_dir                 = f"{base_dir}/wps"                 # Path to compiled WPS folder
wrf_dir                 = f"{base_dir}/wrf/test/em_real"    # Path to compiled WRF em_real folder
wrfout_dir              = f"{base_dir}/wrf_output"          # Path to wrfout folder
namelist_wps_file       = f"{wps_dir}/namelist.wps"         # Path to namelist.wps file
namelist_wrf_file       = f"{wrf_dir}/namelist.input"       # Path to namelist.input file

# GFS Downloader parameters
gfs_num_workers         = 4     # Number of workers will be assigned to download gfs concurrently
gfs_download_increment  = 3     # set to 1 if you want to download gfs dataset for every forecast hours
gfs_left_lon            = 110   # -180 to 180
gfs_right_lon           = 115   # -180 to 180
gfs_top_lat             = -2    # -90 to 90
gfs_bottom_lat          = -5    # -90 to 90

# WPS and WRF parameters
forecast_duration       = 1     # length of simulation days
max_dom                 = 3     # Maximum WPS and WRF domain
num_proc                = 4     # number of CPU cores will be used to execute real.exe & wrf.exe
wrfout_saved_domain     = 3     # which wrfout file will be saved
```

> Note: in order to download GFS dataset for every n hours (eg: every 3 hours), set `gfs_download_increment` to 3.
2. Export libraries path `LD_LIBRARY_PATH` that will be used by wps.exe and wrf.exe.
3. Execute the program by typing `python main.py`

## Credit
Copyright (c) 2020-present <a href="https://github.com/elpahlevi">Reza Pahlevi</a> and <a href="https://github.com/agungbaruna">Agung Baruna Setiawan Noor</a>.