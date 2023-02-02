import os
import sys
import re
import subprocess
import requests
import time
from datetime import date
from concurrent.futures import ThreadPoolExecutor

# Generate list of url, filename, and filepath that will be used by download_gfs_parallel function
def generate_url(folder_path: str, start_date: date, issued_time: str, forecast_time: int, increment: int, left_lon: float, right_lon: float, top_lat: float, bottom_lat: float):
    if forecast_time > 384:
        sys.exit("Error: Forecast time can't be more than 384")
    
    base_url = "https://nomads.ncep.noaa.gov/cgi-bin/"
    year  = str(start_date.year)
    month = str("%02d" % (start_date.month))
    day   = str("%02d" % (start_date.day))

    # Generate list of url, filename, and filepath based on the length of forecast time
    list_url = [f"{base_url}filter_gfs_0p25.pl?file=gfs.t{issued_time}z.pgrb2.0p25.f" + "%03d" % hour + f"&all_lev=on&all_var=on&subregion=&leftlon={str(left_lon)}&rightlon={str(right_lon)}&toplat={str(top_lat)}&bottomlat={str(bottom_lat)}&dir=%2Fgfs.{year}{month}{day}%2F{issued_time}%2Fatmos" for hour in range(0, forecast_time + 1, increment)]
    list_filename = [f"gfs_4_{year}{month}{day}_{issued_time}00_" + "%03d" % hour + ".grb2" for hour in range(0, forecast_time + 1, increment)]
    list_filepath = [f"{folder_path}/{filename}" for filename in list_filename]

    return zip(list_url, list_filename, list_filepath)

# Setup download worker
def download_worker(data):
    start_time = time.time()
    response = requests.get(data[0])
    with open(data[2], "wb") as f:
        f.write(response.content)
    end_time = time.time()
    print(f"{data[1]} has been downloaded in {int(end_time - start_time)} seconds")

# Download GFS data concurrently
def download_gfs(path: str, n_worker: int, start_date: date, issued_time: str, forecast_time: int, increment: int, left_lon: float, right_lon: float, top_lat: float, bottom_lat: float):
    formatted_date = start_date.strftime("%Y-%m-%d")
    folder_path = f"{path}/{formatted_date}"
    if not(os.path.isdir(folder_path)):
        os.makedirs(folder_path)
    print(f"GFS files will be saved in {folder_path}")
    
    data = generate_url(folder_path, start_date, issued_time, forecast_time, increment, left_lon, right_lon, top_lat, bottom_lat)
    with ThreadPoolExecutor(max_workers=n_worker) as executor:
        executor.map(download_worker, data)
    print(f"All GFS files with issued time {issued_time} has been downloaded")

# Read namelist.wps file then replace start_date and end_date value
def change_namelist_wps(start_date: date, end_date: date, namelist_path: str):
    # parse into YYYY-mm-dd format (eg: 2023-01-27)
    current_start  = start_date.strftime("%Y-%m-%d")
    current_end    = end_date.strftime("%Y-%m-%d")

    # Use sed command to change the date value (Credit to : absen22 @github)
    subprocess.run([f"sed -i.backup -r '/^ start_date/s/'2000-01-01_00:00:00'/'{current_start}_00:00:00'/g' {namelist_path}"], shell=True)
    subprocess.run([f"sed -i.backup -r '/^ end_date/s/'2000-01-01_00:00:00'/'{current_end}_00:00:00'/g' {namelist_path}"], shell=True)

    print("namelist.wps file has been updated!") 
    print(f"start_date value changed to {current_start}")
    print(f"end_date value changed to {current_end}")

# Read namelist.input file then replace start_year, start_month, start_day, start_hour, end_year, end_month, end_day, end_hour
def change_namelist_wrf(start_date: date, end_date: date, namelist_path: str):
    current_start_date  = start_date.strftime("%Y-%m-%d").split("-")
    current_end_date    = end_date.strftime("%Y-%m-%d").split("-")
    run_days            = int((end_date - start_date).total_seconds() / 86400)

    # Use sed command to change the date value (Credit to : absen22 @github)
    # change run_days value
    subprocess.run([f"sed -i.backup -r '/^ run_days/s/'0'/'{run_days}'/g' {namelist_path}"], shell=True)

    # change start values
    subprocess.run([f"sed -i.backup -r '/^ start_year/s/'2000'/'{current_start_date[0]}'/g' {namelist_path}"], shell=True)
    subprocess.run([f"sed -i.backup -r '/^ start_month/s/'01'/'{current_start_date[1]}'/g' {namelist_path}"], shell=True)
    subprocess.run([f"sed -i.backup -r '/^ start_day/s/'01'/'{current_start_date[2]}'/g' {namelist_path}"], shell=True)
    
    # change end values
    subprocess.run([f"sed -i.backup -r '/^ end_year/s/'2000'/'{current_end_date[0]}'/g' {namelist_path}"], shell=True)
    subprocess.run([f"sed -i.backup -r '/^ end_month/s/'01'/'{current_end_date[1]}'/g' {namelist_path}"], shell=True)
    subprocess.run([f"sed -i.backup -r '/^ end_day/s/'01'/'{current_end_date[2]}'/g' {namelist_path}"], shell=True)
    
    print("namelist.input file has been updated!")
    print("The model will simulate from {start} to {end}".format(start = start_date.strftime("%d-%m-%Y"), end = end_date.strftime("%d-%m-%Y")))

# Run a step to generate met_em file
def run_wps(wps_path: str, gfsout_path: str, start_date: date):
    # Delete FILE* and met_em* files from previous run
    subprocess.run([f"rm {wps_path}/FILE*"],shell=True)
    subprocess.run([f"rm {wps_path}/met_em*"], shell=True)
    subprocess.run([f"rm {wps_path}/GRIBFILE*"], shell=True)
    subprocess.run([f"rm {wps_path}/geo_em*"], shell=True)
    
    #execute geogrid.exe
    subprocess.run("./geogrid.exe", cwd=wps_path)
    print("geogrid.exe executed")
    
    #create link to GFS data
    gfs_date_folder = start_date.strftime("%Y-%m-%d")
    subprocess.run(["./link_grib.csh", f"{gfsout_path}/{gfs_date_folder}/*"], cwd=wps_path)
    print("Link grib created")
    
    # create link to variable tables
    if os.path.exists(f"{wps_path}/Vtable"):
        print("Linked Vtable.GFS file Exists")
    else:
        subprocess.run(["ln", "-sf" ,f"{wps_path}/ungrib/Variable_Tables/Vtable.GFS", "Vtable"], cwd=wps_path)
        print("Vtable.GFS Symlink created")
    
    #execute ungrib.exe
    subprocess.run("./ungrib.exe", cwd=wps_path)
    
    #execute metgrid.exe
    subprocess.run("./metgrid.exe", cwd=wps_path)

# Run WRF model
def run_wrf(wps_path: str, wrf_path: str, np: int):
    # Delete the met_em files from last simulation
    subprocess.run([f"rm {wrf_path}/met_em*"], shell=True)
    
    # Create symlink to all files named met_em*
    subprocess.run([f"ln -sf {wps_path}/met_em* ."], shell=True, cwd=wrf_path)
    print("All met_em* files has been linked")
    
    # Execute real.exe
    subprocess.run([f"mpirun -np {np} ./real.exe"], shell=True, cwd=wrf_path)
    print("real.exe executed")
    
    # Check the output from real.exe before execute wrf.exe
    rsl_error = subprocess.check_output(["tail --lines 1 rsl.error.0000"], shell=True, cwd=wrf_path)
    if re.search("SUCCESS COMPLETE REAL_EM INIT", str(rsl_error)):
        # Execute wrf.exe
        subprocess.run([f"mpirun -np {np} ./wrf.exe"], shell=True, cwd=wrf_path)
        print("SUCCESS COMPLETE REAL_EM INIT")
    else:
        sys.exit("Check namelist.input")

# Move the output to specific folder based on selected domain
def move_output(wrf_path: str, wrfout_path: str, start_date: date, domain: int):
    wrfout_date = start_date.strftime("%Y-%m-%d")
    folder_path = f"{wrfout_path}/{wrfout_date}"
    if not(os.path.isdir(folder_path)):
        os.makedirs(folder_path)
    
    subprocess.run([f"mv {wrf_path}/wrfout_d0{domain}* {folder_path}/wrfout_d0{domain}_{wrfout_date}.nc"], shell=True, cwd=wrf_path)
    print(f"WRF simulation files on domain {domain} has been saved to {wrfout_path}")