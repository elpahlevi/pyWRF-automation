# PyWRF-Automation
Python automation script to download the Global Forecast System (GFS) data from NOMADS NOAA with spatial resolution 0.25<sup>0</sup> and execute Weather Research & Forecasting (WRF) model.

## Prerequisites
To using this script, you must complete following prerequisites such as:
1. Linux/Unix distribution
2. Python 3.7+
3. MPI Package (OpenMPI/Intel MPI/MPICH)
4. WRF-ARW Model with `em_real` case using `dmpar` compiler selection.

This repository includes two script, which is `main.py` as executable script and `utils.py` as a collection of function that will be used by `main.py` script.

## How to use
1. Open `main.py` file and change the values below `Arguments` comment (line 11):

```python
# Arguments
gfsout_path             = "/home/your_username/wrf_model/gfs_dataset"
wps_path                = "/home/your_username/wrf_model/wps"
wrf_path                = "/home/your_username/wrf_model/wrf/test/em_real"
wrfout_path             = "/home/your_username/wrf_model/wrf_output"
gfs_download_increment  = 1
gfs_left_lon            = 90
gfs_right_lon           = 141
gfs_top_lat             = 8
gfs_bottom_lat          = -13
wrf_forecast_duration   = 1 
wrf_num_proc            = 1
wrfout_domain_data      = 1
```

| Argument               | Data Type | Range                   | Description                                                        | Note                                                                    |
|------------------------|-----------|-------------------------|--------------------------------------------------------------------|-------------------------------------------------------------------------|
| gfsout_path            | str       | -                       | Path to GFS dataset folder                                         | -                                                                       |
| wps_path               | str       | -                       | Path to compiled WPS folder                                        | -                                                                       |
| wrf_path               | str       | -                       | Path to compiled WRF met_em folder                                 | -                                                                       |
| wrfout_path            | str       | -                       | Path to wrfout folder                                              | -                                                                       |
| gfs_download_increment | int       | -                       | Which GFS forecast hours data will be downloaded                   | Set to `1` if you want to download GFS dataset for every forecast hours |
| gfs_left_lon           | float     | -180 to 180             | Longitude                                                          | gfs_left_lon < gfs_right_lon                                            |
| gfs_right_lon          | float     | -180 to 180             | Longitude                                                          | -                                                                       |
| gfs_top_lat            | float     | -90 to 90               | Latitude                                                           | gfs_top_lat > gfs_bottom_lat                                            |
| gfs_bottom_lat         | float     | -90 to 90               | Latitude                                                           | -                                                                       |
| wrf_forecast_duration  | int       | 1 to 16 (in days)       | Length of simulation days                                          | -                                                                       |
| wrf_num_proc           | int       | 1 to `nproc`            | Number of CPU cores will be used to execute `real.exe` & `wrf.exe` | -                                                                       |
| wrfout_domain_data     | int       | 1 to `number_of_domain` | Which wrfout file will be saved                                    | Set to `1` if you want to save wrfout file on domain 1 etc              |

> Note: in order to download GFS dataset for several hours (eg: every 3 hours), set `gfs_download_increment` argument to 3.

2. Open `namelist.wps` file then set `start_date` and `end_date` value to `2000-01-01_00:00:00`.
3. Open `namelist.input` file then set the following variables using this value below:

| Variable    | value |
|-------------|-------|
| run_days    | 0     |
| start_year  | 2000  |
| start_month | 01    |
| start_day   | 01    |
| end_year    | 2000  |
| end_month   | 01    |
| end_day     | 01    |

4. Export `LD_LIBRARY_PATH`
5. Run the program by typing `python main.py`

## Credit
Copyright (c) 2020-present <a href="https://github.com/elpahlevi">Reza Pahlevi</a> and <a href="https://github.com/agungbaruna">Agung Baruna Setiawan Noor</a>.