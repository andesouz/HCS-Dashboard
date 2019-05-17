import datetime
from dashboard import db
from dashboard import login_manager
from flask_login import UserMixin


class CarMaker(db.Model):
    __tablename__ = 'hcs_maker'
    maker_id = db.Column(db.Integer, primary_key=True, autoincrement='auto')
    maker_name = db.Column(db.String(40), index=True)
    carlisting = db.relationship('CarListing', back_populates='maker')
    models = db.relationship('CarModel')

    def __repr__(self):
        return f"CarMaker: {self.maker_id} : {self.maker_name}"


class CarModel(db.Model):
    __tablename__ = 'hcs_model'
    model_id = db.Column(db.Integer, primary_key=True, autoincrement='auto')
    model_name = db.Column(db.String(30), index=True)
    maker_id = db.Column(db.Integer, db.ForeignKey('hcs_maker.maker_id'), index=True)
    carlisting = db.relationship('CarListing', back_populates='model')

    def __repr__(self):
        return f"CarModel: ID: {self.model_id} Model: {self.model_name}  :  Maker_id: {self.maker_id}"


class CarBodyStyle(db.Model):
    __tablename__ = 'hcs_bodystyle'
    bodystyle_id = db.Column(db.Integer, primary_key=True, autoincrement='auto')
    bodystyle_name = db.Column(db.String(40), index=True)
    carlisting = db.relationship('CarListing', back_populates='bodystyle')

    def __repr__(self):
        return f"CarBodyStyle: {self.bodystyle_id} : {self.bodystyle_name}"


class CarListing(db.Model):
    __tablename__ = 'hcs_car'
    uuid = db.Column(db.String(32), primary_key=True)
    vin = db.Column(db.String(17), index=True)
    year_car = db.Column(db.Integer, index=True)
    color_ext = db.Column(db.String(50))
    color_int = db.Column(db.String(50))
    doors = db.Column(db.Integer)
    drivetrain = db.Column(db.String(20))
    engine = db.Column(db.String(30))
    img_src = db.Column(db.String(200))
    mpg_city = db.Column(db.Float)
    mpg_highway = db.Column(db.Float)
    transmission = db.Column(db.String(30))
    trim_car = db.Column(db.String(30))
    classification = db.Column(db.String(20))
    type_car = db.Column(db.String(20))

    model_id = db.Column(db.Integer, db.ForeignKey('hcs_model.model_id'), index=True)
    model = db.relationship('CarModel', back_populates='carlisting')

    maker_id = db.Column(db.Integer, db.ForeignKey('hcs_maker.maker_id'), index=True)
    maker = db.relationship('CarMaker', back_populates='carlisting')

    bodystyle_id = db.Column(db.Integer, db.ForeignKey('hcs_bodystyle.bodystyle_id'), index=True)
    bodystyle = db.relationship('CarBodyStyle', back_populates='carlisting')

    prices = db.relationship('CarPrice', back_populates='car', order_by='CarPrice.date_id.desc()')

    _ROOT_URL = 'https://www.hertzcarsales.com'

    def get_url(self):
        parts = [self.year_car, self.maker.maker_name, self.model.model_name.replace(' ', '+'), self.uuid]
        file = '-'.join(str(x) for x in parts)
        return ''.join([CarListing._ROOT_URL, '/', self.type_car, '/', self.maker.maker_name, '/', file, '.htm'])

    def __repr__(self):
        return f'CarListings: {self.uuid} {self.vin}'
        # {self.maker} {self.model} {self.year_car}


class CarPrice(db.Model):
    __tablename__ = 'hcs_price'
    price_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    price = db.Column(db.Float, default=0, index=True)
    miles = db.Column(db.Integer)
    kbb_price = db.Column(db.Float, default=0)
    kbb_difference = db.Column(db.Float, default=0)
    accountid = db.Column(db.String(40))

    date_id = db.Column(db.Integer, db.ForeignKey('hcs_dateprice.date_id'), index=True)
    date = db.relationship('CarDatePrice', back_populates='price')

    location_id = db.Column(db.Integer, db.ForeignKey('hcs_location.location_id'), index=True)
    location = db.relationship('CarLocation', back_populates='price')

    uuid = db.Column(db.String(32), db.ForeignKey('hcs_car.uuid'), index=True)
    car = db.relationship('CarListing', back_populates='prices')

    def __repr__(self):
        return f'CarPrice: {self.date} ${self.price} diff: ${self.kbb_difference} {self.miles}mi'


class CarDatePrice(db.Model):
    __tablename__ = 'hcs_dateprice'
    date_id = db.Column(db.Integer, primary_key=True, autoincrement='auto')
    date_price = db.Column(db.Date, nullable=False)
    price = db.relationship('CarPrice', back_populates='date')

    def __repr__(self):
        return f'CarDatePrice: {self.date_id}  {self.date_price}'


class CarLocation(db.Model):
    __tablename__ = 'hcs_location'
    location_id = db.Column(db.Integer, primary_key=True, autoincrement='auto')
    city = db.Column(db.String(25))
    state = db.Column(db.String(2))
    zipcode = db.Column(db.Integer)
    price = db.relationship('CarPrice', back_populates='location')

    def __eq__(self, other):
        return all([self.city == other.city, self.state == other.state, self.zipcode == other.zipcode])

    def __repr__(self):
        return f'CarLocation: {self.location_id} {self.city} {self.state} {self.zipcode}'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'hcs_user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(60), nullable=False)
    image_src = db.Column(db.String(25), nullable=False, default='user_default.png')
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    date_deactivated = db.Column(db.DateTime, nullable=True, default=None)
    last_password_change = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    # Valid Status:  0 -> Inactive, 1 -> Active
    status = db.Column(db.Integer, nullable=False, default=1)

    def __repr__(self):
        return f"User: '{self.username}', '{self.email}'  status: {self.status}"
