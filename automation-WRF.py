""" 
WRF-ARW Model & GFS Automation System using Python 3
Credit : Muhamad Reza Pahlevi (@elpahlevi on Github) & Agung Baruna Setiawan Noor (@absen22 on Github)
If you find any trouble, reach the author on email : elpahlevi@hotmail.com 
"""

import os, datetime, pycurl, certifi, subprocess, glob, re
from os import sep
from dateutil.relativedelta import relativedelta

#set directory
dir = os.getcwd()
namelist_wps_file = dir + "/WPS/namelist.wps"
namelist_wrf_file = dir + "/WRF/test/em_real/namelist.input"

#get today date
dt    = datetime.datetime.today()
year  = str(dt.year)
month = str("%02d" % (dt.month))
day   = str("%02d" % (dt.day))

#to imagine how the schema below works, just imagine this script was executed on September 23st 2020 (run for 7 days prediction) and running everyday
prev_start_date = dt + relativedelta(days=-1)
prev_end_date   = dt + relativedelta(days=6)
start_date      = dt + relativedelta(days=0)
end_date        = dt + relativedelta(days=7)

# Download the GFS file on 0.25 degree grid resolution based on defined region
def downloadGFS(issued_time, forecast_time, left_lon, right_lon, top_lat, bottom_lat):
    base_URL = "https://nomads.ncep.noaa.gov/cgi-bin/"

    #Generate the urls and file name based on forecast_time parameter
    hours = ["%03d" % hrs for hrs in range(0, forecast_time, 3)]
    get_URL = [f"{base_URL}filter_gfs_0p25.pl?file=gfs.t{issued_time}z.pgrb2.0p25.f" + "%03d" % hour + f"&all_lev=on&all_var=on&subregion=&leftlon={str(left_lon)}&rightlon={str(right_lon)}&toplat={str(top_lat)}&bottomlat={str(bottom_lat)}&dir=%2Fgfs.{year}{month}{day}%2F{issued_time}" for hour in range(0, forecast_time, 3)]
    files_name = [f"gfs_4_{year}{month}{day}_{issued_time}00_" + "%03d" % hour + ".grb2" for hour in range(0, forecast_time, 3)]

    # download all files using pycurl
    folder_location = dir + "/GFS_data/" + str(year + "-" + month + "-" + day + "/")
    if not(os.path.isdir(folder_location)): #Check if Directory exist
        os.makedirs(folder_location)
    print(f"GFS files will be saved in {folder_location}")
    for url, filename, hours in zip(get_URL, files_name, hours):
        if os.path.exists(folder_location + filename): #Check if GFS file fxist
            print("File Exists")
            continue
        with open(folder_location + filename, 'wb') as f:
            curl_download = pycurl.Curl()
            curl_download.setopt(curl_download.URL, url)
            curl_download.setopt(curl_download.CAINFO, certifi.where())
            curl_download.setopt(curl_download.WRITEDATA, f)
            curl_download.perform()
            curl_download.close()
        print(f"GFS file on {day}-{month}-{year} on issued time {issued_time} and forecast time {str(hours)} has been downloaded")
    print(f"All GFS files with issued time {issued_time} downloaded")

#read namelist.wps on WPS folder then replace start_date, GFS folder path, and end_date value based from GFS data
def changeNamelistWPS(namelist_file):
    prev_start_date_wps = str(prev_start_date.strftime("%Y-%m-%d"))
    prev_end_date_wps   = str(prev_end_date.strftime("%Y-%m-%d"))
    start_date_wps      = str(start_date.strftime("%Y-%m-%d"))
    end_date_wps        = str(end_date.strftime("%Y-%m-%d"))

    #use sed command and f-string format to change the date value (Credit to : absen22 @github)
    subprocess.run([f"sed -i.backup -r '/^ start_date/s/'{prev_start_date_wps}_00:00:00'/'{start_date_wps}_00:00:00'/g' {namelist_file}"], shell=True)
    subprocess.run([f"sed -i.backup -r '/^ end_date/s/'{prev_end_date_wps}_18:00:00'/'{end_date_wps}_18:00:00'/g' {namelist_file}"], shell=True)
    print("namelist.wps file has been changed!") 

#read namelist.input on em_real folder (WRF/em_real) then replace start_year, start_month, start_day, start_hour, end_year, end_month, end_day, end_hour
def changeNameListWRF(namelist_file):
    #determine previous start date then split into year, month, day
    prev_start_year_wrf = str(prev_start_date.year)
    prev_start_month_wrf = str("%02d" % prev_start_date.month)
    prev_start_day_wrf = str("%02d" % prev_start_date.day)
    
    #determine previous end date then split into year, month, day
    prev_end_year_wrf = str(prev_end_date.year)
    prev_end_month_wrf = str("%02d" % prev_end_date.month)
    prev_end_day_wrf = str("%02d" %  prev_end_date.day)
    
    #determine current start date
    start_year_wrf = str(start_date.year)
    start_month_wrf = str("%02d" % start_date.month)
    start_day_wrf = str("%02d" % start_date.day)
    
    #determine current end date
    end_year_wrf = str(end_date.year)
    end_month_wrf = str("%02d" % end_date.month)
    end_day_wrf = str("%02d" % end_date.day)

    #use sed command and f-string format to change the date value (Credit to : absen22 @github)
    #change the start parameters
    subprocess.run([f"sed -i.backup -r '/^ start_year/s/'{prev_start_year_wrf}'/'{start_year_wrf}'/g' {namelist_file}"], shell=True)
    subprocess.run([f"sed -i.backup -r '/^ start_month/s/'{prev_start_month_wrf}'/'{start_month_wrf}'/g' {namelist_file}"], shell=True)
    subprocess.run([f"sed -i.backup -r '/^ start_day/s/'{prev_start_day_wrf}'/'{start_day_wrf}'/g' {namelist_file}"], shell=True)
    
    #change the end parameters
    subprocess.run([f"sed -i.backup -r '/^ end_year/s/'{prev_end_year_wrf}'/'{end_year_wrf}'/g' {namelist_file}"], shell=True)
    subprocess.run([f"sed -i.backup -r '/^ end_month/s/'{prev_end_month_wrf}'/'{end_month_wrf}'/g' {namelist_file}"], shell=True)
    subprocess.run([f"sed -i.backup -r '/^ end_day/s/'{prev_end_day_wrf}'/'{end_day_wrf}'/g' {namelist_file}"], shell=True)
    
    print("namelist.input file has been changed!") 
    print("The model will simulate from {start} to {end}".format(start = start_date.strftime("%d-%m-%Y"), end = end_date.strftime("%d-%m-%Y")))

def runWPS():
    #Delete FILE* and met_em* files from previous run
    delete_file = dir + "/WPS"
    subprocess.run([f"rm {delete_file}/FILE*"],shell=True)
    subprocess.run([f"rm {delete_file}/met_em*"], shell=True)
    subprocess.run([f"rm {delete_file}/GRIBFILE*"], shell=True)
    
    #execute geogrid.exe
    geo_files = glob.glob(dir + "/WPS/geo_em*")
    if not(os.path.exists(geo_files[0])): #Check geo_em*
        subprocess.run("./geogrid.exe", cwd=dir + "/WPS")
        print("----------------------------Geogrid.exe executed----------------------------")
    
    #create link to GFS data
    gfs_date_folder = start_date.strftime("%Y-%m-%d")
    subprocess.run(["./link_grib.csh", f"{dir}/GFS_data/{gfs_date_folder}/*"], cwd=dir + "/WPS")
    print("Link grib created")
    
    #create link to variable tables
    if os.path.exists(dir + "/WPS/Vtable"): #Check if GFS file fxist
        print("Linked Vtable.GFS file Exists")
    else:
        subprocess.run(["ln", "-sf", "ungrib/Variable_Tables/Vtable.GFS Vtable"], cwd=dir + "/WPS/")
        print("Vtable.GFS Symlink created")
    
    #execute ungrib.exe
    subprocess.run("./ungrib.exe", cwd=dir + "/WPS")
    
    #execute metgrid.exe
    subprocess.run("./metgrid.exe", cwd=dir + "/WPS")

def runWRF(n_processor):
    #create link to all files named met_em*
    subprocess.run([f"ln -sf {dir}/WPS/met_em* ."], shell=True, cwd=dir + "/WRF/test/em_real/")
    print("All met_em* files has been linked")
    
    #execute real.exe
    subprocess.run([f"mpirun -np {str(n_processor)} ./real.exe"], shell=True, cwd=dir + "/WRF/test/em_real/")
    print("real.exe executed")
    
    #check the output from real.exe before execute wrf.exe
    rsl_error = subprocess.check_output(["tail --lines 1 rsl.error.0000"], shell=True, cwd=dir + "/WRF/test/em_real/")
    if re.search("SUCCESS COMPLETE REAL_EM INIT", str(rsl_error)):
        #execute wrf.exe
        subprocess.run([f"mpirun -np {str(n_processor)} ./wrf.exe"], shell=True, cwd=dir + "/WRF/test/em_real/")
        print("SUCCESS COMPLETE REAL_EM INIT")
    else:
        print("Check namelist.input")

#Run the Code
downloadGFS(issued_time = "00", forecast_time = 193, left_lon=95, right_lon=141, top_lat=6, bottom_lat=-11)
changeNamelistWPS(namelist_file = namelist_wps_file)
changeNameListWRF(namelist_file = namelist_wrf_file)
runWPS()
runWRF(n_processor=4)
