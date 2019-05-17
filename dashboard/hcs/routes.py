import datetime
from flask import Blueprint
from flask import request
from flask import current_app
from flask_login import login_required
from dashboard import db
from dashboard.models import CarListing
from dashboard.models import CarPrice
from dashboard.models import CarMaker
from dashboard.models import CarModel
from dashboard.models import CarDatePrice
from dashboard.models import CarBodyStyle
from dashboard.hcs.utils import render_template_app
from dashboard.hcs.utils import add_filters

hcs = Blueprint('hcs', __name__)


@hcs.route("/")
@hcs.route("/home")
def home():

    return render_template_app('home.html',
                               menu_active='hcs.home')


@hcs.route("/active_listings")
def active_listings():
    page = request.args.get('page', 1, type=int)

    # Query database for latest date we have prices available - using SQLAlchemy
    latest_date = db.session.query(CarDatePrice). \
        order_by(db.desc(CarDatePrice.date_price)).first()

    query = db.session.query(CarPrice). \
        filter(CarPrice.date_id == latest_date.date_id). \
        filter(CarPrice.price > 0). \
        join(CarListing). \
        join(CarDatePrice). \
        join(CarBodyStyle). \
        join(CarModel). \
        join(CarMaker). \
        order_by(CarPrice.price)

    query, filters, form_data = add_filters(query, request.args)

    data = query.paginate(page=page, per_page=current_app.config['PAGINATION_PAGE_SIZE'], )

    return render_template_app('display.html',
                               data=data,
                               latest_date=latest_date.date_price,
                               menu_active='hcs.active_listings',
                               title='All Active Listings',
                               filters=filters,
                               form_data=form_data)


@hcs.route("/price_drops")
def price_drops():
    page = request.args.get('page', 1, type=int)

    # Query database for latest date we have prices available - using SQLAlchemy
    dates = db.session.query(CarDatePrice). \
        order_by(db.desc(CarDatePrice.date_id)).limit(2).all()
    latest_date = dates[0]
    day_before = dates[1]

    changed = db.session.\
        query(CarPrice.uuid.label('uuid'),
              (db.func.max(CarPrice.price) - db.func.min(CarPrice.price)).label('price_diff'),
              db.func.min(CarPrice.price).label('minimum_price')).\
        join(CarDatePrice).\
        filter(db.or_(CarPrice.date_id == latest_date.date_id,
                      CarPrice.date_id == day_before.date_id)).\
        group_by(CarPrice.uuid).\
        having(db.and_(db.func.max(CarPrice.price) != db.func.min(CarPrice.price),
                       db.func.min(CarPrice.price) > 0)).subquery()

    query = db.session.\
        query(CarPrice).add_columns(changed.c.price_diff).\
        filter(CarPrice.date_id == latest_date.date_id).\
        join(changed, CarPrice.uuid == changed.c.uuid).\
        filter(CarPrice.price == changed.c.minimum_price).\
        join(CarListing, CarModel, CarMaker, CarBodyStyle).\
        join(CarDatePrice).\
        order_by(db.desc(changed.c.price_diff))

    query, filters, form_data = add_filters(query, request.args)

    data = query.paginate(page=page, per_page=current_app.config['PAGINATION_PAGE_SIZE'], )

    return render_template_app('display.html',
                               data=data,
                               latest_date=latest_date.date_price,
                               menu_active='hcs.price_drops',
                               title='Latest Price Drops Report',
                               filters=filters,
                               form_data=form_data)


@hcs.route("/new_listings")
def new_listings():
    page = request.args.get('page', 1, type=int)
    latest_date = db.session.query(CarDatePrice).order_by(db.desc(CarDatePrice.date_id)).limit(1).first()

    one_price_cars = db.session.query(CarPrice.uuid). \
        having(db.and_(db.func.count(CarPrice.price_id) == 1,
                       db.func.max(CarPrice.date_id) == latest_date.date_id)). \
        group_by(CarPrice.uuid). \
        subquery()

    query = db.session.query(CarPrice). \
        filter(CarPrice.date_id == latest_date.date_id). \
        filter(CarPrice.price > 0). \
        join(one_price_cars, one_price_cars.c.uuid == CarPrice.uuid). \
        join(CarListing, CarModel, CarMaker, CarBodyStyle). \
        order_by(CarPrice.price)

    query, filters, form_data = add_filters(query, request.args)

    data = query.paginate(page=page, per_page=current_app.config['PAGINATION_PAGE_SIZE'], )

    return render_template_app('display.html',
                               data=data,
                               latest_date=latest_date.date_price,
                               menu_active='hcs.new_listings',
                               title='New Listings',
                               filters=filters,
                               form_data=form_data)


@hcs.route("/re-listings")
def re_listings():
    page = request.args.get('page', 1, type=int)

    dates = db.session.query(CarDatePrice).order_by(db.desc(CarDatePrice.date_id)).limit(2).all()
    dte = dates[0]
    dte_b = dates[1]

    last_day_listings = db.session.query(CarPrice.uuid). \
        filter(CarPrice.date_id == dte_b.date_id).subquery()

    d = db.session.query(CarPrice.uuid). \
        group_by(CarPrice.uuid). \
        having(
        db.and_(
            (db.func.max(CarPrice.date_id) - db.func.min(CarPrice.date_id)) >
            db.func.count(CarPrice.price_id),
            db.func.max(CarPrice.date_id) == dte.date_id,
            CarPrice.uuid.notin_(last_day_listings)
        )).subquery()

    query = db.session.query(CarPrice). \
        filter(CarPrice.date_id == dte.date_id). \
        join(d, d.c.uuid == CarPrice.uuid). \
        join(CarListing, CarModel, CarMaker, CarBodyStyle)

    query, filters, form_data = add_filters(query, request.args)

    data = query.paginate(page=page, per_page=current_app.config['PAGINATION_PAGE_SIZE'], )

    return render_template_app('display.html',
                               data=data,
                               latest_date=dte.date_price,
                               menu_active='hcs.re_listings',
                               title='Re-listed Vehicles',
                               filters=filters,
                               form_data=form_data)


@hcs.route("/best_deals")
@login_required
def best_deals():
    # handle filters
    page = request.args.get('page', 1, type=int)
    latest_date = db.session.query(CarDatePrice).order_by(CarDatePrice.date_id.desc()).first()

    query = db.session.query(CarPrice). \
        filter(CarPrice.kbb_difference > 0). \
        filter(CarPrice.date_id == latest_date.date_id). \
        order_by((CarPrice.kbb_difference / CarPrice.kbb_price).desc()). \
        join(CarListing, CarModel, CarMaker, CarBodyStyle)

    query, filters, form_data = add_filters(query, request.args)

    data = query.paginate(page=page, per_page=current_app.config['PAGINATION_PAGE_SIZE'], )

    return render_template_app('best_deals.html',
                               data=data,
                               latest_date=latest_date.date_price,
                               menu_active='hcs.best_deals',
                               title='Best Deals',
                               filters=filters,
                               form_data=form_data)


@hcs.route("/cardetails/<car_uuid>")
def car_details(car_uuid):
    data = CarListing.query.\
        filter(CarListing.uuid == car_uuid).\
        join(CarBodyStyle).\
        join(CarModel).\
        join(CarMaker).first()

    return render_template_app('car_details.html', car=data)


@hcs.route("/statistics")
def statistics():
    data_range = db.session.query(CarDatePrice).order_by(db.desc(CarDatePrice.date_id)).all()
    start_date = data_range[-1]
    end_date = data_range[0]

    tables = list()

    # Vehicle count per Model and Maker
    table = dict()
    table['table_headers'] = ['Maker', 'Model', 'Vehicle Count']
    table['table_rows'] = db.session. \
        query(CarMaker.maker_name, CarModel.model_name, db.func.count(CarListing.uuid).label('Count')). \
        join(CarModel, CarMaker.maker_id == CarModel.maker_id). \
        join(CarListing, CarListing.model_id == CarModel.model_id). \
        group_by(CarMaker.maker_id, CarModel.model_id). \
        order_by(db.desc('Count')).all()
    table['table_title'] = 'Statistics per Model/Maker'
    tables.append(table)

    # Vehicle Count by Manufacturer
    table = dict()
    table['table_headers'] = ['Maker', 'Vehicle Count']
    table['table_rows'] = db.session. \
        query(CarMaker.maker_name, db.func.count(CarListing.uuid).label('Count')). \
        join(CarListing). \
        group_by(CarMaker.maker_id). \
        order_by(db.desc('Count')).all()
    table['table_title'] = 'Number of Vehicles per Manufacturer'
    tables.append(table)

    return render_template_app('statistics.html',
                               latest_date=datetime.date.today(),
                               tables=tables,
                               start_date=start_date.date_price,
                               end_date=end_date.date_price,
                               menu_active='hcs.statistics')


@hcs.route("/about")
def about():
    return render_template_app('about.html', menu_active='hcs.about')
