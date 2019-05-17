from flask import Blueprint
from flask import current_app as app
from flask_restful import Resource
from flask_restful import Api
from flask_restful import reqparse
from flask_restful import inputs
from flask_restful import abort
from dashboard import db
from dashboard.models import CarListing
from dashboard.models import CarBodyStyle
from dashboard.models import CarMaker
from dashboard.models import CarDatePrice
from dashboard.models import CarPrice
from dashboard.models import CarModel
from dashboard.models import CarLocation
from common.models import ScrapedData

api_bp = Blueprint('api', __name__)
api = Api(api_bp)


class ApiData(Resource):

    # get and put Not implemented by design
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('count',
                            type=inputs.int_range(1, 100),
                            required=True,
                            help=' ',
                            location='json')
        parser.add_argument('api_key', required=True, help=' ', location='json')
        parser.add_argument('rows', type=list, required=True, help=' ', location='json')
        data = parser.parse_args(strict=True, http_error_code=400)

        if len(data['rows']) != data['count']:
            abort(400)

        if data['api_key'] != app.config['API_KEY']:
            abort(403)

        hcs_data = ScrapedData()
        hcs_data_attrs = [s for s in dir(hcs_data) if not s.startswith('_')]
        new_car_count = 0

        for listing_data in data['rows']:

            for attr in hcs_data_attrs:
                setattr(hcs_data, attr, listing_data[attr])

            car = db.session.query(CarListing).filter(CarListing.uuid == hcs_data.uuid).first()
            if not car:
                # new car found
                new_car_count += 1
                car = CarListing(uuid=hcs_data.uuid,
                                 vin=hcs_data.vin,
                                 classification=hcs_data.classification,
                                 color_ext=hcs_data.color_ext,
                                 color_int=hcs_data.color_int,
                                 drivetrain=hcs_data.drivetrain,
                                 engine=hcs_data.engine,
                                 img_src=hcs_data.img_src,
                                 transmission=hcs_data.transmission,
                                 trim_car=hcs_data.trim,
                                 type_car=hcs_data.type)
                try:
                    car.doors = int(hcs_data.doors)
                except (ValueError, TypeError):
                    car.doors = 0
                try:
                    car.mpg_city = float(hcs_data.mpg_city)
                except (ValueError, TypeError):
                    car.mpg_city = 0
                try:
                    car.mpg_highway = float(hcs_data.mpg_highway)
                except (ValueError, TypeError):
                    car.mpg_highway = 0
                try:
                    car.year_car = float(hcs_data.year)
                except (ValueError, TypeError):
                    car.year_car = 0

                maker = db.session.query(CarMaker).filter(CarMaker.maker_name == hcs_data.make).first()
                car.maker = maker if maker else CarMaker(maker_name=hcs_data.make)

                model = db.session.query(CarModel).filter(CarModel.model_name == hcs_data.model).first()
                car.model = model if model else CarModel(model_name=hcs_data.model, maker_id=car.maker.maker_id)

                bodystyle = db.session.query(CarBodyStyle). \
                    filter(CarBodyStyle.bodystyle_name == hcs_data.bodystyle).first()
                car.bodystyle = bodystyle if bodystyle else CarBodyStyle(bodystyle_name=hcs_data.bodystyle)

                db.session.add(car)

            price = CarPrice(accountid=hcs_data.accountid,
                             kbb_difference=hcs_data.kbb_difference if hcs_data.kbb_difference else 0,
                             kbb_price=hcs_data.kbb_price if hcs_data.kbb_price else 0,
                             miles=hcs_data.miles,
                             price=hcs_data.price if hcs_data.price else 0)

            price.uuid = car.uuid
            price.car = car

            date_price = db.session.query(CarDatePrice).filter(CarDatePrice.date_price == hcs_data.date).first()
            price.date = date_price if date_price else CarDatePrice(date_price=hcs_data.date)
            price.date_id = price.date.date_id

            location = db.session.query(CarLocation). \
                filter(db.and_(CarLocation.city == hcs_data.city,
                               CarLocation.state == hcs_data.state,
                               CarLocation.zipcode == hcs_data.zipcode)).first()
            price.location = location if location else CarLocation(city=hcs_data.city,
                                                                   state=hcs_data.state,
                                                                   zipcode=hcs_data.zipcode)

            db.session.add(price)

        db.session.commit()
        return {'status': 1,
                'newListings': len(data['rows']),
                'newCars': new_car_count}, 200


api.add_resource(ApiData, '/hcs/api/v1.0/data')



