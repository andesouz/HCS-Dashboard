import os
import requests
import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException


class Driver(webdriver.Firefox):
    """Context Manager for Firefox Webdriver"""
    def __init__(self, WEB_DRIVER_PATH):
        # add path to webdriver to PATH environment
        os.environ['PATH'] += os.pathsep + WEB_DRIVER_PATH
        # set options
        options = Options()
        options.headless = True
        super().__init__(options=options)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def hcs_execute(WAIT_TIME, WEB_DRIVER_PATH, SEARCH_AREA_ZIP_CODE, SEARCH_AREA_DISTANCE, DataClass, logger):
    """
    Create selenium driver and execute website scraper.

    Returns list with all car listings found.
    The return list contains ScraperData objects.
    """
    with Driver(WEB_DRIVER_PATH) as driver:
        # Configurations
        zip_code = SEARCH_AREA_ZIP_CODE
        distance_miles = SEARCH_AREA_DISTANCE
        driver.get(f'https://www.hertzcarsales.com/used-cars-for-sale.htm?geoZip={zip_code}&geoRadius={distance_miles}')

        # data attributes to look for .... inner li
        data_car_attributes = ('data-uuid', 'data-vin', 'data-year', 'data-make', 'data-model',
                               'data-bodystyle', 'data-trim', 'data-doors', 'data-drivetrain', 'data-engine',
                               'data-transmission', 'data-type', 'data-classification')
        data_price_attributes = ('data-accountid', 'data-city', 'data-state', 'data-zipcode')

        all_data = []
        page_count = 1
        # main discovery loop
        while True:
            # find form - find each <li> data container tag in current page
            # lis = driver.find_elements_by_xpath("//form[@id='compareForm']/div/ul/li")
            try:
                X = "//form[@id='compareForm']/div/ul/li"
                lis = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_all_elements_located((By.XPATH, X)))
            except TimeoutException as e:
                logger.error('Could not locate list of cars (lis). Results may be partial: ' + str(type(e)) + str(e))
                return all_data

            for li in lis:
                data_car = []
                try:
                    for p in data_car_attributes:
                        data_car.append(li.get_attribute(p))
                except (StaleElementReferenceException, Exception) as e:
                    logger.error('Could not scrape car attributes:  ' + str(type(e)) + str(e))
                    continue

                row = DataClass()
                row.uuid, row.vin, row.year, row.make, *data_car = data_car
                row.model, row.bodystyle, row.trim, row.doors, *data_car = data_car
                row.drivetrain, row.engine, row.transmission, row.type, row.classification = data_car

                data_price = []
                try:
                    for p in data_price_attributes:
                        data_price.append(li.get_attribute(p))
                except (StaleElementReferenceException, Exception) as e:
                    logger.error('Could not scrape price attributes:  ' + str(type(e)) + str(e))
                    continue

                try:
                    # click for details
                    X = "div/div[@class='simple-info']"
                    div = WebDriverWait(li, WAIT_TIME).until(EC.presence_of_element_located((By.XPATH, X)))
                    X = "div[@class='simple-btn-wrap']/a"
                    a = WebDriverWait(div, WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, X)))
                    a.click()
                except Exception as e:
                    logger.error('Could not click for details:  ' + str(type(e)) + str(e))
                    continue
                try:
                    lst = div.text.split('\n')
                except StaleElementReferenceException as e:
                    logger.error('StaleElementReferenceException trying to lst = div.text.split("\\n")')
                    continue

                miles = mpg_city = mpg_highway = None
                color_ext = color_int = ''
                fields = map(str.strip, lst[1].split('•'))
                for f in fields:
                    if f.startswith('Mileage'):
                        miles = int(f.split()[1].replace(',', ''))
                    elif f.startswith('Exterior'):
                        color_ext = ' '.join(f.split()[2:])
                    elif f.startswith('Interior'):
                        color_int = ' '.join(f.split()[2:])
                    elif f.startswith('MPG'):
                        mpg = ' '.join(f.split()[2:])
                        mpg_city, mpg_highway = map(float, mpg.split('/'))
                row.color_ext, row.color_int = color_ext, color_int
                row.mpg_city, row.mpg_highway = mpg_city, mpg_highway

                kbb_price = kbb_difference = price = None
                for idx in range(3, 10, 2):
                    try:
                        label = lst[idx]
                        if label.startswith('KBB'):
                            try:
                                kbb_price = int(lst[idx + 1].strip().replace('$', '').replace(',', ''))
                            except ValueError:
                                logger.info(f'NoData: {row.vin}  Non number kbb price {row.model}')
                        elif label.startswith('Price'):
                            try:
                                kbb_difference = int(lst[idx + 1].strip().replace('$', '').replace(',', ''))
                            except ValueError:
                                logger.info(f'NoData: {row.vin}  Non number kbb diff {row.model}')
                        elif label.startswith('No Haggle'):
                            try:
                                price = int(lst[idx + 1].strip().replace('$', '').replace(',', ''))
                            except ValueError:
                                logger.info(f'NoData: {row.vin}  No price {row.model}')
                    except IndexError as e:
                        # may not have all lines. That's fine.
                        break

                try:
                    X = 'div/div/div/div/div[1]/img[1]'
                    img = WebDriverWait(li, WAIT_TIME).until(EC.presence_of_element_located((By.XPATH, X)))
                    img_src = img.get_attribute('src')
                except (NoSuchElementException, TimeoutException, StaleElementReferenceException, Exception) as e:
                    logger.info('Error finding image: ' + str(type(e)) + ' : ' + str(e))
                    img_src = None
                row.img_src = img_src.split('?')[0] if img_src else None

                row.miles = miles
                row.price = price
                row.date = datetime.date.today()
                row.kbb_difference = kbb_difference
                row.kbb_price = kbb_price
                row.accountid, row.city, row.state, row.zipcode = data_price

                all_data.append(row)

            logger.info(f'Finished Page {page_count}')
            page_count += 1

            try:
                # Hit pagination next for more cars, if exception ... we are done
                X = '//div[@class="pagination"]/span[@class="next"]/a'
                next_page = WebDriverWait(driver, WAIT_TIME).until(EC.element_to_be_clickable((By.XPATH, X)))
                next_page.click()
            except ElementClickInterceptedException:
                logger.info('Reached end of pagination list gracefully')
                break
            except NoSuchElementException as e:
                logger.error('Page Error, may not have completed list:::\n' + str(e))
                break
            except Exception as e:
                logger.error('Unexpected Error, may not have completed list:::\n' + str(e))
                break

    return all_data


def hcs_upload_data_api(data_upload, api_url, api_key, post_number_rows_per_message, logger, DataClass):

    payload = dict()
    payload['api_key'] = api_key
    data_attrs = [s for s in dir(DataClass()) if not s.startswith('__')]
    num_rows = len(data_upload)
    pointer = 0
    while pointer < num_rows:

        data_sliced = data_upload[pointer:pointer + post_number_rows_per_message]
        pointer += post_number_rows_per_message

        payload['count'] = len(data_sliced)

        rows = []
        for values in data_sliced:
            row = {}
            for attr, value in zip(data_attrs, values):
                row[attr] = value
            rows.append(row)

        payload['rows'] = rows

        # call API - POST
        r = requests.post(api_url, json=payload)
        rj = r.json()
        if rj.get('status', 0) == 1:
            logger.info(f'Success, pointer:{pointer}')
            logger.info(f"New Cars: {rj.get('newCars', 'None')}  NewListings: {rj.get('newListings', 'None')}")
        else:
            logger.error(f'Oops: something went wrong, pointer: {pointer}')
            return False

    return True