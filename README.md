Hertz Car Sales Dashboard
=========================

HCS Dashboard is a data enhancement dashboard design to make easier finding “good deals” at the Hertz Car sales website. It provides some enhancements over the set of filters available at the source website, including historical data on pricing, price drops and ranking of best deals as compared to Kelly Blue Book pricing. 

**Requirements:**

Make sure you have the proper version of Geckodriver to your Firefox installation.
You can download geckodriver at https://github.com/mozilla/geckodriver/releases

Use pipenv to install all dependencies. Pipfile.lock is included. 

    $ pipenv install


HCS Dashboard is comprised of two parts:
-  HCS Dashboard Flask Web Application
-  HCS Scraper

HCS Dashboard Flask Web Application
-------------------------------
Web portal based on Python Flask micro web framework. Here we list some of the application components:
- PostgreSQL: Choice of database for this project.
- Flask-SQLAlchemy: Flask wrapper for SQLAlchemy. The ORM layer is used extensively
- Flask-Restful: A REST-API was implemented to allow database updates from a remote machine. As the system is currently deployed, the scraper does not run in the same web server machine.
- Jinja2: Template language used.
- VueJS: JavaScript framework for client functionality, like filters.
- Nginx and Gunicorn: Deployment: Nginx as a reverse proxy and Gunicorn as Python WSGI HTTP server.

**Run Flask**

    $ python run_flask.py

HCS Scraper
------------

The Hertz Car Sales website is heavily dependent on JavaScript. Therefore, it cannot be scraped with lightweight HTML only libraries. We use Selenium with Python bindings and Firefox WebDriver. The scraper runs once a day. Check hcs_scraper.py in the code base. 

**Running Script:**

    $ python run_hcs_script.py -s <True | False> -p /path/to/configuration/file/config.ini
 -s      Flag for skipping Scraper and only uploading existind CSV files to Server via API 
 
 -p      Path to configuration file

**Configuration File:**

    DATA_PATH = /path/to/where/csv/files/go       ; Path to store csv backup files and compressed files after upload.
    WEB_DRIVER_PATH = /path/to/webdriver/hcs-scraper    ; Path to Geckodriver
    URL_API = 'http://127.0.0.1:5000/api/v1.0/data'     ; URL to Flask Dashboard Server
    API_KEY = 1234567891                                ; Your unique API key
    ROWS_PER_MESSAGE = 50            ; number of car listing sent on each API post
    WAIT_TIME = 15    ; default webdriver wait if website not responsive - seconds
    SEARCH_AREA_ZIP_CODE = 92129
    SEARCH_AREA_DISTANCE = 100     ; distance in miles


