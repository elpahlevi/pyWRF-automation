from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os, shutil, sys, re, subprocess, requests, time, logging

# For logging purposes
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# Setup download worker
def gfs_download_worker(data):
    if not os.path.exists(data[1]):
        start_time = time.time()
        response = requests.get(data[0])
        with open(data[1], "wb") as f:
            f.write(response.content)
        end_time = time.time()
        logging.info(f"INFO: GFS Downloader - {Path(data[1]).name} has been downloaded in {int(end_time - start_time)} seconds")
    else:
        logging.info(f"INFO: GFS Downlaoder - File {Path(data[1]).name} is already exist, skipped")

# Download GFS dataset concurrently
def download_gfs(path: str, n_worker: int, start_date: datetime, forecast_time: int, increment: int, cycle_time: str, left_lon: float, right_lon: float, top_lat: float, bottom_lat: float):
    if forecast_time > 384:
        sys.exit("ERROR: GFS Downloader - Forecast time can't be more than 384")
    
    folder_path = f"{path}/{start_date.strftime('%Y-%m-%d')}"
    base_url = "https://nomads.ncep.noaa.gov/cgi-bin"
    year  = str(start_date.year)
    month = str("%02d" % (start_date.month))
    day   = str("%02d" % (start_date.day))

    if not(os.path.isdir(folder_path)):
        os.makedirs(folder_path)
    logging.info(f"INFO: GFS Downloader - Dataset will be saved in {folder_path}")

    list_url = [f"{base_url}/filter_gfs_0p25.pl?file=gfs.t{cycle_time}z.pgrb2.0p25.f{'%03d' % hour}&all_lev=on&all_var=on&subregion=&leftlon={str(left_lon)}&rightlon={str(right_lon)}&toplat={str(top_lat)}&bottomlat={str(bottom_lat)}&dir=%2Fgfs.{year}{month}{day}%2F{cycle_time}%2Fatmos" for hour in range(0, forecast_time + 1, increment)]
    list_filepath = [f"{folder_path}/gfs_4_{year}{month}{day}_{cycle_time}00_{'%03d' % hour}.grb2" for hour in range(0, forecast_time + 1, increment)]

    with ThreadPoolExecutor(max_workers = n_worker) as executor:
        executor.map(gfs_download_worker, zip(list_url, list_filepath))
    logging.info(f"INFO: GFS Downloader - Dataset with cycle time {cycle_time} has been downloaded")

def run_wps(wps_path: str, gfs_path: str, namelist_wps_path: str, max_dom: int, start_date: datetime, end_date: datetime, opts = None):
    wps_params = {
        "max_dom": str(max_dom),
        "start_date": start_date.strftime("%Y-%m-%d_%H:%M:%S"),
        "end_date": end_date.strftime("%Y-%m-%d_%H:%M:%S")
    }
    
    if opts:
        wps_params.update(opts)

    for key in ["parent_id", "parent_grid_ratio", "i_parent_start", "j_parent_start", "e_we", "e_sn"]:
        value = wps_params.get(key)
        if value != None and len(value.split(",")) != max_dom:
            sys.exit(f"Error: WPS - length of {key} value is not matched to max_dom parameter")

    with open(namelist_wps_path, "r") as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            for variable, value in wps_params.items():
                matched = re.search(rf"{variable}\s*=\s*[^,]+,", line)
                if matched:
                    index_of_equal_sign = line.find("=")

                    if variable in ["wrf_core", "map_proj", "geog_data_path", "out_format", "prefix", "fg_name"]:
                        lines[i] = f"{line[:index_of_equal_sign + 1]} '{value}',\n"
                        continue

                    if variable in ["start_date", "end_date", "geog_data_res"]:
                        formatted = f"'{value}',"
                        lines[i] = f"{line[:index_of_equal_sign + 1]} {formatted * max_dom}\n"
                        continue
                    
                    lines[i] = f"{line[:index_of_equal_sign + 1]} {str(value)},\n"

    with open(namelist_wps_path, "w") as file:
        file.writelines(lines)
    
    logging.info(f"INFO: WPS - Configuration file updated")

    # Delete FILE* and met_em* files from previous run
    subprocess.run([f"rm {wps_path}/FILE*"],shell=True)
    subprocess.run([f"rm {wps_path}/PFILE*"], shell=True)
    subprocess.run([f"rm {wps_path}/met_em*"], shell=True)
    subprocess.run([f"rm {wps_path}/GRIBFILE*"], shell=True)
    subprocess.run([f"rm {wps_path}/geo_em*"], shell=True)

    # Execute geogrid.exe
    subprocess.run("./geogrid.exe", cwd=wps_path)
    logging.info("INFO: WPS - geogrid.exe completed")

    # Create a link to GFS dataset
    subprocess.run(["./link_grib.csh", f"{gfs_path}/{start_date.strftime('%Y-%m-%d')}/*"], cwd=wps_path)
    logging.info("INFO: WPS - GFS dataset linked successfully")

    # Create a symlink to GFS Variable Table
    if os.path.exists(f"{wps_path}/Vtable"):
        logging.info("INFO: WPS - Vtable.GFS is already linked")
    else:
        subprocess.run(["ln", "-sf" ,f"{wps_path}/ungrib/Variable_Tables/Vtable.GFS", "Vtable"], cwd=wps_path)
        logging.info("INFO: WPS - Symlink of Vtable.GFS created")
    
    # Execute ungrib.exe
    subprocess.run("./ungrib.exe", cwd=wps_path)
    logging.info("INFO: WPS - ungrib.exe completed")

    # Execute metgrid.exe
    subprocess.run("./metgrid.exe", cwd=wps_path)
    logging.info("INFO: WPS - metgrid.exe completed")

    logging.info("INFO: WPS - Process completed. met_em files is ready")

def run_wrf(wps_path: str, wrf_path: str, wrfout_path: str, namelist_input_path: str, run_days: int, max_dom: int, start_date: datetime, end_date: datetime, num_proc: int, wrfout_saved_domain: int, opts = None):
    wrf_params = {
        "run_days": str(run_days),
        "start_year": str(start_date.year),
        "start_month": "%02d" % start_date.month,
        "start_day": "%02d" % start_date.day,
        "start_hour": "%02d" % start_date.hour,
        "end_year": str(end_date.year),
        "end_month": "%02d" % end_date.month,
        "end_day": "%02d" % end_date.day,
        "end_hour": "%02d" % end_date.hour,
        "max_dom": str(max_dom)
    }
    if opts:
        wrf_params.update(opts)

    for key in ["e_we", "e_sn", "e_vert", "dx", "dy", "grid_id", "parent_id", "i_parent_start", "j_parent_start", "parent_grid_ratio", "parent_time_step_ratio"]:
        value = wrf_params.get(key)
        if value != None and len(value.split(",")) != max_dom:
            sys.exit(f"Error: WRF Model - length of {key} value is not matched to max_dom parameter")

    with open(namelist_input_path, "r") as file:
        lines = file.readlines()

        for i, line in enumerate(lines):
            for variable, value in wrf_params.items():
                matched = re.search(rf"{variable}\s*=\s*[^,]+,", line)
                if matched:
                    index_of_equal_sign = line.find("=")
                    
                    # Change time_control parameter
                    if variable in ["start_year", "start_month", "start_day", "start_hour", "end_year", "end_month", "end_day", "end_hour"]:
                        lines[i] = f"{line[:index_of_equal_sign + 1]} {((value + ', ') * max_dom)}\n"
                        continue

                    lines[i] = f"{line[:index_of_equal_sign + 1]} {value},\n"

    with open(namelist_input_path, "w") as file:
        file.writelines(lines)

    logging.info("INFO: WRF Model - Configuration file updated")
    logging.info(f"INFO: WRF Model - Model will take a simulation from {start_date.strftime('%Y-%m-%d_%H:%M:%S')} to {end_date.strftime('%Y-%m-%d_%H:%M:%S')}")

    # Delete unused files from previous run
    subprocess.run([f"rm {wrf_path}/met_em*"], shell=True)
    subprocess.run([f"rm {wrf_path}/wrfout*"], shell=True)
    subprocess.run([f"rm {wrf_path}/wrfrst*"], shell=True)

    # Create a new symlink to all metgrid files from WPS folder
    subprocess.run([f"ln -sf {wps_path}/met_em* ."], shell=True, cwd=wrf_path)
    logging.info("INFO: WRF Model - met_em* files has been linked")

    # Execute real.exe
    subprocess.run([f"mpirun -np {num_proc} ./real.exe"], shell=True, cwd=wrf_path)
    logging.info("INFO: WRF Model - real.exe executed")

    # Check the output from real.exe before execute wrf.exe
    rsl_error = subprocess.check_output(["tail --lines 1 rsl.error.0000"], shell=True, cwd=wrf_path)
    if re.search("SUCCESS COMPLETE REAL_EM INIT", str(rsl_error)):
        # Execute wrf.exe
        subprocess.run([f"mpirun -np {num_proc} ./wrf.exe"], shell=True, cwd=wrf_path)
        logging.info("INFO: WRF Model - Simulation completed")
    else:
        sys.exit("Error: WRF Model - Check namelist.input configuration")

    # Move output to assigned location
    wrfout_folder_path = f"{wrfout_path}/{start_date.strftime('%Y-%m-%d')}"
    if not(os.path.isdir(wrfout_folder_path)):
        os.makedirs(wrfout_folder_path)
    
    subprocess.run([f"mv {wrf_path}/wrfout_d0{wrfout_saved_domain}* {wrfout_folder_path}/wrfout_d0{wrfout_saved_domain}_{start_date}.nc"], shell=True, cwd=wrf_path)
    logging.info(f"INFO: WRF Model - Simulation files on domain {wrfout_saved_domain} has been saved to {wrfout_folder_path}")

# Calculate execution time
def calculate_execution_time(start: float, stop: float):
    if stop - start < 60:
        execution_duration = ("%1d" % (stop - start))
        logging.info(f"INFO: Automation - Process completed in {execution_duration} seconds")
        sys.exit(0)
    elif stop - start < 3600:
        execution_duration = ("%1d" % ((stop - start) / 60))
        logging.info(f"INFO: Automation - Process completed in {execution_duration} minutes")
        sys.exit(0)
    else:
        execution_duration = ("%1d" % ((stop - start) / 3600))
        logging.info(f"INFO: Automation - Process complete in {execution_duration} hours")
        sys.exit(0)