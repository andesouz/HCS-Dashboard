"""
HCS Scraper Script
Implements Hertz Car sales scraper as of May 2019. Any changes on website may break this scraper. Make sure you
install all dependencies before running script.

Running Script:
$ python run_hcs_scraper.py -s <True | False> -p /path/to/configuration/file/config.ini
-s      Flag for skipping Scraper and only uploading existing CSV files to Server via API
-p      Absolute path to configuration file

Configuration File:
DATA_PATH = /path/to/where/csv/files/go       ; Path to store csv backup files and compressed files after upload.
WEB_DRIVER_PATH = /path/to/webdriver/hcs_scraper    ; Path to Geckodriver
URL_API = 'http://127.0.0.1:5000/api/v1.0/data'     ; URL to Flask Dashboard Server
API_KEY = 1234567891                                ; Your unique API key
ROWS_PER_MESSAGE = 50            ; number of car listing sent on each API post
WAIT_TIME = 15    ; default webdriver wait if website not responsive - seconds

Requirements:
Make sure you have the proper version of Geckodriver to your Firefox installation.
You can download geckodriver at https://github.com/mozilla/geckodriver/releases
"""
import os
import sys
from time import sleep
import datetime
import getopt
import logging
import csv
import subprocess
from configparser import ConfigParser
from common.models import ScrapedData
from hcs_scraper import hcs_scraper

help_txt = """
Command line options:
-s <False|True>     Skip scraping function. Just update server with any existing csv file.
-p <path>           Path to configuration file. If none, config.ini local folder.
"""
skip_scraping = False
configuration_file = 'hcs_scraper/config.ini'
try:
    optlist, args = getopt.getopt(sys.argv[1:], 's:p:', [])

    for opt, value in optlist:
        if opt == '-s':
            skip_scraping = True if value == 'True' else False
        if opt == '-p':
            configuration_file = value

except getopt.GetoptError as e:
    print(f'Default settings used: {configuration_file}')
    print('Not skipping scraper')

# Read configuration file
try:
    with open(configuration_file, 'r') as file:
        config = ConfigParser()
        config.read_file(file)

except FileNotFoundError as e:
    print(e)
    sys.exit(-1)

try:
    DATA_PATH = config['APPLICATION']['DATA_PATH']
    WEB_DRIVER_PATH = config['APPLICATION']['WEB_DRIVER_PATH']
    URL_API = config['APPLICATION']['URL_API']
    API_KEY = config['APPLICATION']['API_KEY']
    ROWS_PER_MESSAGE = int(config['APPLICATION']['ROWS_PER_MESSAGE'])
    # seconds - wait till condition is meet before webdriver throws an exception
    WAIT_TIME = float(config['APPLICATION']['WAIT_TIME'])
    SEARCH_AREA_ZIP_CODE = config['APPLICATION']['SEARCH_AREA_ZIP_CODE']
    SEARCH_AREA_DISTANCE = config['APPLICATION']['SEARCH_AREA_DISTANCE']
except Exception as e:
    print(f'Problem with configuration file {configuration_file}')
    print(e)
    sys.exit(-1)

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

all_data = []
RETRY_MAX = 3
if not skip_scraping:
    logger.info('Begin Scraping www.hertzcarsales.com')
    retry_count = 1
    while retry_count <= RETRY_MAX:
        all_data = hcs_scraper.hcs_execute(WAIT_TIME,
                                           WEB_DRIVER_PATH,
                                           SEARCH_AREA_ZIP_CODE,
                                           SEARCH_AREA_DISTANCE,
                                           ScrapedData,
                                           logger)
        if all_data:
            break
        else:
            logger.error('Error detected, waiting 5min before retry')
            sleep(60 * 5)
            logger.info(f'Retrying {retry_count} of {RETRY_MAX}')
            retry_count += 1

    if not all_data:
        logger.error('Scraper Failed All Retries! Terminate')
        sys.exit(-1)

    logger.info(f"Scraper finished gracefully, {len(all_data)} listings found")
else:
    logger.info('Skipping Scraper Flag On')

# Create csv file with today's listings
if all_data:
    logger.info('Creating csv file')
    csv_filename = DATA_PATH + f'/hcs-{str(datetime.date.today())}.csv'
    with open(csv_filename, 'w') as file:
        w = csv.writer(file, quoting=csv.QUOTE_ALL)
        web_data_attr = [s for s in dir(ScrapedData()) if not s.startswith('__')]
        w.writerow(web_data_attr)
        w.writerows(([getattr(row, p, '') for p in web_data_attr] for row in all_data))
    logger.info(f"Finished creating csv file: {csv_filename}")
else:
    logger.info('No data to create csv file, skipped')

# read all files in folder and filter out non csv ones
files = sorted(os.listdir(DATA_PATH))
all_csv_files = [fn for fn in files if os.path.splitext(fn)[1] == '.csv']

if all_csv_files:
    for idx, f_name in enumerate(all_csv_files, 1):
        logger.info(f'Reading csv file {f_name}   {idx} of {len(all_csv_files)}')

        absolute_path_filename = ''.join([DATA_PATH, '/', f_name])
        with open(absolute_path_filename, 'r') as f:
            csv_reader = csv.reader(f, quoting=csv.QUOTE_ALL)
            # Discard header
            _ = next(csv_reader)
            all_data = [row for row in csv_reader]

        logger.info(f"Connecting with Server API: {URL_API}")
        status = hcs_scraper.hcs_upload_data_api(
            all_data,
            URL_API,
            API_KEY,
            ROWS_PER_MESSAGE,
            logger,
            ScrapedData)

        # if data successfully uploaded, compress csv file and delete original file
        if status:
            try:
                resp = subprocess.run(['tar',
                                       '-czf',
                                       absolute_path_filename + '.tar.gz',
                                       absolute_path_filename], check=True)
            except subprocess.CalledProcessError as e:
                resp = False
                logger.error(f"Could not compress file: {absolute_path_filename}")

            if resp:
                logger.info(f'Created file {absolute_path_filename}')
                try:
                    cmd = subprocess.run(['rm',
                                          absolute_path_filename], check=True)
                except subprocess.CalledProcessError as e:
                    logger.error(f"Could not delete file: {absolute_path_filename}")

logger.info('Finished Updating Server - Closing')
sys.exit()
