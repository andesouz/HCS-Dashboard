class ScrapedData:
    """Data class used to model data fields from hcs website. It includes all fields available"""
    def __init__(self):
        self.uuid = None
        self.vin  = None
        self.year = None
        self.make = None
        self.model = None
        self.bodystyle = None
        self.trim = None
        self.doors = None
        self.drivetrain = None
        self.engine = None
        self.transmission = None
        self.type = None
        self.classification = None
        self.img_src = None
        self.color_int = None
        self.color_ext = None
        self.mpg_city = None
        self.mpg_highway = None
        self.miles = None
        self.price = None
        self.kbb_price = None
        self.kbb_difference = None
        self.date = None
        self.accountid = None
        self.city = None
        self.zipcode = None
        self.state = None

    def __repr__(self):
        return f'{self.__class__.split(".")[-1]} {self.year} {self.make} {self.model} ${self.price}'
