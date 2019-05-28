"""
Configuration file for HCS Flask Web Application
"""
class Config:

    SECRET_KEY = 'yourownverysecretkey'

    SQLALCHEMY_DATABASE_URI = 'postgresql://dbuser:userpassword@localhost:5432/your_db_name'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # record all queries ... for debug only ... print query stats is footer
    SQLALCHEMY_RECORD_QUERIES = False
	# Number of car listings per page
    PAGINATION_PAGE_SIZE = 48
	# Key to access Server API
    API_KEY = '1111111111'


