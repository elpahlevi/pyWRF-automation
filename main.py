""" 
WRF-ARW Model & GFS Automation System using Python 3
Credit : Muhamad Reza Pahlevi (@elpahlevi) & Agung Baruna Setiawan Noor (@agungbaruna)
If you find any trouble, reach the author via email : mr.levipahlevi@gmail.com 
"""

import time
import datetime as dt
import utils

# Arguments
gfsout_folder_path      = "/home/your_username/wrf_model/gfs_dataset"      # Path to GFS dataset folder
wps_folder_path         = "/home/your_username/wrf_model/wps"              # Path to compiled WPS folder
wrf_folder_path         = "/home/your_username/wrf_model/wrf/test/em_real" # Path to compiled WRF em_real folder
wrfout_folder_path      = "/home/your_username/wrf_model/wrf_output"       # Path to wrfout folder
gfs_num_workers         = 4     # Number of workers will be assigned to download gfs concurrently
gfs_download_increment  = 3     # set to 1 if you want to download gfs dataset for every forecast hours
gfs_left_lon            = 110   # -180 to 180
gfs_right_lon           = 115   # -180 to 180
gfs_top_lat             = -2    # -90 to 90
gfs_bottom_lat          = -5    # -90 to 90
wrf_forecast_duration   = 1     # length of simulation days
num_proc                = 1     # number of CPU cores will be used to execute real.exe & wrf.exe
wrfout_domain_data      = 1     # which wrfout file will be saved

# Get current time when script is executed
start_time = time.time()

# Set start_date, end_date, and forecast_time
start_date              = dt.datetime.today() - dt.timedelta(days = 1)
end_date                = start_date + dt.timedelta(days = wrf_forecast_duration)
delta_in_seconds        = (end_date - start_date).total_seconds()
gfs_forecast_time       = int(delta_in_seconds / 3600)

# Path to namelist.wps, namelist.input file
namelist_wps_file   = f"{wps_folder_path}/namelist.wps"
namelist_wrf_file   = f"{wrf_folder_path}/namelist.input"

# Execute functions
utils.download_gfs(gfsout_folder_path, gfs_num_workers, start_date, "00", gfs_forecast_time, gfs_download_increment, gfs_left_lon, gfs_right_lon, gfs_top_lat, gfs_bottom_lat)
utils.download_gfs(gfsout_folder_path, gfs_num_workers, start_date, "06", gfs_forecast_time, gfs_download_increment, gfs_left_lon, gfs_right_lon, gfs_top_lat, gfs_bottom_lat)
utils.download_gfs(gfsout_folder_path, gfs_num_workers, start_date, "12", gfs_forecast_time, gfs_download_increment, gfs_left_lon, gfs_right_lon, gfs_top_lat, gfs_bottom_lat)
utils.download_gfs(gfsout_folder_path, gfs_num_workers, start_date, "18", gfs_forecast_time, gfs_download_increment, gfs_left_lon, gfs_right_lon, gfs_top_lat, gfs_bottom_lat)
utils.change_namelist_wps(start_date, end_date, namelist_wps_file)
utils.change_namelist_wrf(start_date, end_date, namelist_wrf_file)
utils.run_wps(wps_folder_path, gfsout_folder_path, start_date)
utils.run_wrf(wps_folder_path, wrf_folder_path, num_proc)
utils.move_output(wrf_folder_path, wrfout_folder_path, start_date, wrfout_domain_data)

# Calculate execution time
end_time = time.time()
if end_time - start_time < 60:
    execution_duration = ("%1d" % (end_time - start_time))
    print(f"Process completed in {execution_duration} seconds")
    exit(0)
elif end_time - start_time < 3600:
    execution_duration = ("%1d" % ((end_time - start_time) / 60))
    print(f"Process completed in {execution_duration} minutes")
    exit(0)
else:
    execution_duration = ("%1d" % ((end_time - start_time) / 3600))
    print(f"Process complete in {execution_duration} hours")
    exit(0)