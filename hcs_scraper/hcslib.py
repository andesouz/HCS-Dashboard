""" HCS classes:
    Car: Represents individual car in our system
    Price: Represents each unique collection of price/mileage overtime
"""


class Car:
    _ROOT_URL = 'https://www.hertzcarsales.com'

    __slots__ = ['accountid', 'uuid', 'vin', 'year', 'make', 'model', 'bodystyle', 'trim',
                 'doors', 'drivetrain', 'engine', 'transmission', 'type', 'classification',
                 'zipcode', 'city', 'state', 'img_src', 'color_int', 'color_ext', 'mpg_city',
                 'mpg_highway']  # , 'url'

    def __init__(self, data, img_src=None):
        if len(data) < 17:
            raise ValueError('Car missing Data')

        self.accountid, self.uuid, self.vin, self.year, *data = data
        self.make, self.model, self.bodystyle, self.trim, *data = data
        self.doors, self.drivetrain, self.engine, self.transmission, *data = data
        self.type, self.classification, self.zipcode, self.city,  self.state = data
        self.img_src = img_src

        self.color_int = self.color_ext = None
        self.mpg_city = None
        self.mpg_highway = None

    def get_url(self):
        file = '-'.join([self.year, self.make, self.model.replace(' ', '+'), self.uuid])
        return ''.join([Car._ROOT_URL, '/', self.type, '/', self.make, '/', file, '.htm'])


class Price:
    __slots__ = ['miles', 'price', 'kbb_price', 'kbb_difference', 'date']

    def __init__(self, miles, price, date, kbb_price=None, kbb_difference=None):
        self.miles = miles
        self.price = price
        self.kbb_price = kbb_price
        self.kbb_difference = kbb_difference
        self.date = date

    def __repr__(self):
        return f'Date: {self.date} Price: {self.price} Miles: {self.miles} KBB:{self.kbb_price}'


class HcsCar:
    _ROOT_URL = 'https://www.hertzcarsales.com'

    __slots__ = ['uuid', 'vin', 'year', 'make', 'model', 'bodystyle', 'trim',
                 'doors', 'drivetrain', 'engine', 'transmission', 'type', 'classification',
                 'img_src', 'color_int', 'color_ext', 'mpg_city', 'mpg_highway']

    def __init__(self, data, img_src=None):
        if len(data) < 13:
            raise ValueError('Car missing Data')

        self.uuid, self.vin, self.year, *data = data
        self.make, self.model, self.bodystyle, self.trim, *data = data
        self.doors, self.drivetrain, self.engine, self.transmission, *data = data
        self.type, self.classification = data
        self.img_src = img_src

        self.color_int = self.color_ext = None
        self.mpg_city = None
        self.mpg_highway = None

    def get_url(self):
        file = '-'.join([self.year, self.make, self.model.replace(' ', '+'), self.uuid])
        return ''.join([HcsCar._ROOT_URL, '/', self.type, '/', self.make, '/', file, '.htm'])


class HcsPrice:
    __slots__ = ['miles', 'price', 'kbb_price', 'kbb_difference', 'date', 'accountid', 'city',
                 'zipcode', 'state']

    def __init__(self, miles, price, date, data_price, kbb_price=None, kbb_difference=None):
        self.miles = miles
        self.price = price
        self.kbb_price = kbb_price
        self.kbb_difference = kbb_difference
        self.date = date
        self.accountid, self.city, self.state, self.zipcode = data_price

    def __repr__(self):
        return f'Date: {self.date} Price: {self.price} Miles: {self.miles} KBB:{self.kbb_price}'
