""" 
WRF-ARW Model & GFS Automation System using Python 3
Credit : Muhamad Reza Pahlevi (@elpahlevi) & Agung Baruna Setiawan Noor (@agungbaruna)
If you find any trouble, reach the author via email : mr.levipahlevi@gmail.com 
"""

from datetime import datetime, timedelta
import utils, time

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

# Time parameters
start_time              = time.time()
current_date            = datetime.today()
start_date              = (current_date - timedelta(days = 1)).replace(hour = 0, minute = 0, second = 0)
end_date                = start_date + timedelta(days = forecast_duration)
forecast_time           = int((end_date - start_date).total_seconds() / 3600) + 6

# Automation Sequences
for cycle_time in ["00", "06", "12", "18"]:
    utils.download_gfs(gfs_dir, gfs_num_workers, start_date, forecast_time, gfs_download_increment, cycle_time, gfs_left_lon, gfs_right_lon, gfs_top_lat, gfs_bottom_lat)
utils.run_wps(wps_dir, gfs_dir, namelist_wps_file, max_dom, start_date, end_date)
utils.run_wrf(wps_dir, wrf_dir, wrfout_dir, namelist_wrf_file, forecast_duration, max_dom, start_date, end_date, num_proc, wrfout_saved_domain)
utils.calculate_execution_time(start_time, time.time())