import os
import psycopg2
from collections import namedtuple
from configparser import ConfigParser


class HcsDb(object):
    def __init__(self, username=None, password=None, database=None, host='localhost', logger=None):

        self.host = host
        self.logger = logger

        username_ini = password_ini = database_ini = None
        parser = ConfigParser()
        parser.read('database.ini')
        if parser.has_section('postgresql'):
            psql = parser['postgresql']
            username_ini, password_ini, database_ini = psql['user'], psql['password'], psql['database']

        param = ['username', 'password', 'database']
        os_keys = ('HCS_USERNAME', 'HCS_PASSWORD', 'HCS_DATABASE')
        try:
            for p, k in zip(param, os_keys):
                if eval(f'{p}'):
                    exec(f'self.{p} = {p}')
                elif eval(f'{p}_ini'):
                    exec(f'self.{p} = {p}_ini')
                else:
                    exec(f'self.{p} = os.environ[{k}]')
        except Exception as e:
            raise ValueError('HcsDb cannot find: username, password and/or database \n' + str(e))

        try:
            self.conn = psycopg2.connect(host=self.host,
                                         database=self.database,
                                         user=self.username,
                                         password=self.password)
        except Exception as e:
            raise ConnectionError('Database Connection: \n' + str(e))

        self.cur = self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.cur.close()
        self.conn.close()

    def create_tables(self):
        """ Create tables for HCS Dashboard"""
        commands = (
            """
            CREATE TABLE IF NOT EXISTS hcs_car (
                vin VARCHAR(17),
                color_ext VARCHAR(50),
                color_int VARCHAR(50), 
                doors INTEGER,
                drivetrain VARCHAR(20),
                engine VARCHAR(30),
                img_src VARCHAR(200),
                model VARCHAR(30),
                mpg_city FLOAT,
                mpg_highway FLOAT,
                transmission VARCHAR(30),
                trim_car VARCHAR(30),
                uuid VARCHAR(32),
                year_car INTEGER,
                bodystyle VARCHAR(40),
                classification VARCHAR(20),
                maker VARCHAR(40), 
                type_car VARCHAR(20),
                PRIMARY KEY (vin, uuid)
            )                        
            """,
            """
            CREATE TABLE IF NOT EXISTS hcs_price (
                price_id SERIAL PRIMARY KEY,
                date_price DATE NOT NULL,
                kbb_price FLOAT NULL,
                kbb_difference FLOAT NULL,
                price FLOAT NOT NULL,
                accountid VARCHAR(40),
                city VARCHAR(25),
                miles INTEGER,
                zipcode INTEGER,
                state VARCHAR(2),              
                vin VARCHAR(17) NOT NULL,
                uuid VARCHAR(32) NOT NULL,
                FOREIGN KEY (vin, uuid)
                    REFERENCES hcs_car (vin, uuid)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS hcs_user (
                user_id INT SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                email VARCHAR(200) NOT NULL,
                password VARCHAR(100) NOT NULL,
                date_created DATE NOT NULL 
            )
            """
            )

        try:
            # cursor = self.conn.cursor()
            cursor = self.cur
            for command in commands:
                cursor.execute(command)
            # cursor.close()
            self.conn.commit()

        except psycopg2.DatabaseError as e:
            msg = 'Fail to Create Database Tables \n' + str(e)
            if self.logger:
                self.logger.error(msg)
            raise Exception(msg)

        return True

    def get_all_cars_vin(self):
        command = """ SELECT vin FROM hcs_car """
        try:
            # cursor = self.conn.cursor()
            cursor = self.cur
            cursor.execute(command)
            resp = {x[0] for x in cursor.fetchall() if x}
        except (psycopg2.DatabaseError, Exception) as e:
            resp = None
            if self.logger:
                self.logger.error('get_all_cars_vin: ' + str(type(e)) + ' ::: ' + str(e))
        return resp

    def get_all_cars_uuid(self):
        command = """ SELECT uuid FROM hcs_car """
        try:
            # cursor = self.conn.cursor()
            cursor = self.cur
            cursor.execute(command)
            resp = {x[0] for x in cursor.fetchall() if x}
        except (psycopg2.DatabaseError, Exception) as e:
            resp = None
            if self.logger:
                self.logger.error('get_all_cars_uuid: ' + str(type(e)) + ' ::: ' + str(e))
        return resp

    def get_prices_cars_by_date(self, target_date):
        # command = """SELECT hcs_price.price_id, hcs_price.date_price, hcs_price.kbb_price,
        # hcs_price.kbb_difference , hcs_price.price , hcs_price.accountid, hcs_price.city,
        # hcs_price.miles, hcs_price.zipcode, hcs_price.state, hcs_price.vin, hcs_price.uuid,
        # hcs_car.vin, hcs_car.img_src, hcs_car.uuid, hcs_car.maker, hcs_car.model
        # FROM hcs_price JOIN hcs_car ON hcs_price.uuid = hcs_car.uuid
        # WHERE hcs_price.date_price = '%s';""" % target_date
        command = """SELECT hcs_price.*, hcs_car.* 
        FROM hcs_price JOIN hcs_car ON hcs_price.uuid = hcs_car.uuid 
        WHERE (hcs_price.date_price = '%s' AND hcs_price.price > 0) 
        ORDER BY hcs_price.price ASC;""" % target_date

        parm_list = ('price_id', 'date_price', 'kbb_price', 'kbb_difference',
                     'price', 'accountid', 'city', 'miles', 'zipcode',
                     'state', 'vin_price', 'uuid_price',
                     'vin_car', 'color_ext', 'color_int', 'doors',
                     'drivetrain', 'engine', 'img_src', 'model',
                     'mpg_city',  'mpg_highway', 'transmission',
                     'trim', 'uuid_car', 'year', 'bodystyle',
                     'classification', 'maker', 'type_car')
        CarData = namedtuple('CarData', parm_list)

        try:
            self.cur.execute(command)
            resp = self.cur.fetchall()
        except (psycopg2.DatabaseError, Exception) as e:
            resp = None
            if self.logger:
                self.logger.error('get_prices_cars_by_date: ' + str(type(e)) + ' ::: ' + str(e))

        if resp:
            resp = [CarData(*x) for x in resp]

        return resp

    def insert_car(self, car):
        resp = True
        # cursor = self.conn.cursor()
        cursor = self.cur
        # handle numeric fields that may not be available
        try:
            int(car.doors)
        except (ValueError, TypeError):
            car.doors = '0'
        try:
            float(car.mpg_city)
        except (ValueError, TypeError):
            car.mpg_city = '0'
        try:
            float(car.mpg_highway)
        except (ValueError, TypeError):
            car.mpg_highway = '0'
        try:
            int(car.year)
        except (ValueError, TypeError):
            car.year = '0'
        # Create values array
        values = []
        values += [f'{car.vin}', f'{car.color_ext}', f'{car.color_int}', f'{car.doors}', f'{car.drivetrain}']
        values += [f'{car.engine}', f'{car.img_src}', f'{car.model}', f'{car.mpg_city}', f'{car.mpg_highway}']
        values += [f'{car.transmission}', f'{car.trim}', f'{car.uuid}', f'{car.year}', f'{car.bodystyle}', ]
        values += [f'{car.classification}', f'{car.make}', f'{car.type}']

        command = """INSERT INTO hcs_car(vin, color_ext, color_int, doors, drivetrain, engine, img_src ,
                                        model, mpg_city, mpg_highway, transmission, trim_car, uuid, year_car, 
                                        bodystyle, classification, maker, type_car)
                     VALUES({});""".format(','.join([' %s'] * len(values)))

        try:
            cursor.execute(command, values)
            self.conn.commit()
        except psycopg2.DatabaseError as e:
            if self.logger:
                self.logger.info('insert_car: ' + str(type(e)) + ' : ' + str(e))
            self.conn.rollback()
            resp = False
        # finally:
        # cursor.close()
        return resp

    def insert_price(self, price, car):
        resp = True
        # cursor = self.conn.cursor()
        cursor = self.cur

        # handle numeric fields that may not be available
        try:
            float(price.kbb_price)
        except (ValueError, TypeError):
            price.kbb_price = '0'
        try:
            float(price.kbb_difference)
        except (ValueError, TypeError):
            price.kbb_difference = '0'
        try:
            float(price.price)
        except (ValueError, TypeError):
            price.price = '0'
        # Create values array
        values = []
        values += [f'{price.date}', f'{price.kbb_price}', f'{price.kbb_difference}', f'{price.price}']
        values += [f'{price.accountid}',  f'{price.city}', f'{price.miles}', f'{price.zipcode}']
        values += [f'{price.state}', f'{car.vin}', f'{car.uuid}']

        command = """INSERT INTO hcs_price( date_price, kbb_price, kbb_difference, price, accountid, city,
                                            miles, zipcode, state, vin, uuid)
                     VALUES({});""".format(','.join([' %s'] * len(values)))
        try:
            cursor.execute(command, values)
        except psycopg2.DatabaseError as e:
            if self.logger:
                self.logger.error('insert_price: ' + str(type(e)) + ' : ' +
                                  str(e) + '  vin:' + f'{car.vin}' + ' uuid:' + f'{car.uuid}')
            self.conn.rollback()
            resp = False

        self.conn.commit()
        # cursor.close()
        return resp

    def insert_prices(self, prices, cars, block_size=20):
        count_prices = 0
        # cursor = self.conn.cursor()
        cursor = self.cur

        prices_length = len(prices)
        slice_start = slice_end = 0
        while slice_end < prices_length:

            slice_end = slice_start + block_size if (slice_start + block_size) < prices_length else prices_length
            prices_slice = prices[slice_start:slice_end]
            cars_slice = cars[slice_start:slice_end]

            rows = []
            for price, car in zip(prices_slice, cars_slice):

                # handle numeric fields that may not be available
                try:
                    float(price.kbb_price)
                except (ValueError, TypeError):
                    price.kbb_price = '0'
                try:
                    float(price.kbb_difference)
                except (ValueError, TypeError):
                    price.kbb_difference = '0'
                try:
                    float(price.price)
                except (ValueError, TypeError):
                    price.price = '0'

                # Create values array
                values = []
                values += [f'{price.date}', f'{price.kbb_price}', f'{price.kbb_difference}', f'{price.price}']
                values += [f'{price.accountid}', f'{price.city}', f'{price.miles}', f'{price.zipcode}']
                values += [f'{price.state}', f'{car.vin}', f'{car.uuid}']
                rows.append('(' + ','.join(["'{}'"] * len(values)).format(*values) + ')')

            command = """INSERT INTO hcs_price( date_price, kbb_price, kbb_difference, price, accountid, city,
                                                miles, zipcode, state, vin, uuid)
                         VALUES {};""".format(','.join([' {}'] * len(rows))).format(*rows)

            exception_flag = False
            try:
                cursor.execute(command)
                self.conn.commit()
                count_prices += (slice_end - slice_start)
            except psycopg2.DatabaseError as e:
                if self.logger:
                    self.logger.error('insert_price: ' + str(type(e)) + ' : ' +
                                      str(e) + '  vin:' + f'{car.vin}' + ' uuid:' + f'{car.uuid}')
                self.conn.rollback()
                exception_flag = True
                resp = False

            # if failed, try one row at a time
            if exception_flag:
                for price, car in zip(prices_slice, cars_slice):
                    resp = self.insert_price(price, car)
                    if resp:
                        count_prices += 1

            slice_start += block_size

        return count_prices


# """
# CREATE TABLE IF NOT EXISTS hcs_bodystyle (
#     bodystyle VARCHAR(40) PRIMARY KEY
# )
# """,
# """
# CREATE TABLE IF NOT EXISTS hcs_classification (
#     classification VARCHAR(20) PRIMARY KEY
# )
# """,
# """
# CREATE TABLE IF NOT EXISTS hcs_maker (
#     maker VARCHAR(40) PRIMARY KEY
# )
# """,
# """
# CREATE TABLE IF NOT EXISTS hcs_state (
#     state VARCHAR(2) PRIMARY KEY
# )
# """,
# """
# CREATE TABLE IF NOT EXISTS hcs_type (
#     type_car VARCHAR(20) PRIMARY KEY
# )
# """,
# """
# CREATE TABLE IF NOT EXISTS hcs_car (
#     vin VARCHAR(17) PRIMARY KEY,
#     color_ext VARCHAR(50),
#     color_int VARCHAR(50),
#     doors INTEGER,
#     drivetrain VARCHAR(20),
#     engine VARCHAR(30),
#     img_src VARCHAR(200),
#     model VARCHAR(30),
#     mpg_city FLOAT,
#     mpg_highway FLOAT,
#     transmission VARCHAR(30),
#     trim_car VARCHAR(30),
#     uuid VARCHAR(32),
#     year_car INTEGER,
#     bodystyle VARCHAR(40),
#     FOREIGN KEY (bodystyle)
#         REFERENCES hcs_bodystyle (bodystyle)
#         ON UPDATE CASCADE,
#     classification VARCHAR(20),
#     FOREIGN KEY (classification)
#         REFERENCES hcs_classification (classification)
#         ON UPDATE CASCADE,
#     maker VARCHAR(40),
#     FOREIGN KEY (maker)
#         REFERENCES hcs_maker (maker)
#         ON UPDATE CASCADE,
#     type_car VARCHAR(20),
#     FOREIGN KEY (type_car)
#         REFERENCES hcs_type (type_car)
#         ON UPDATE CASCADE
# )
# """,
# """
# CREATE TABLE IF NOT EXISTS hcs_price (
#     price_id SERIAL PRIMARY KEY,
#     date_price DATE NOT NULL,
#     kbb_price FLOAT NULL,
#     kbb_difference FLOAT NULL,
#     price FLOAT NOT NULL,
#     accountid VARCHAR(40),
#     city VARCHAR(25),
#     miles INTEGER,
#     zipcode INTEGER,
#     state VARCHAR(2),
#     FOREIGN KEY (state)
#         REFERENCES hcs_state (state)
#         ON UPDATE CASCADE,
#     vin VARCHAR(17) NOT NULL,
#     FOREIGN KEY (vin)
#         REFERENCES hcs_car (vin)
# )
# """
