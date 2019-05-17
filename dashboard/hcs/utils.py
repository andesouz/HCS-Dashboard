from collections import OrderedDict
from dashboard import db
from flask import render_template
from flask import current_app
from dashboard.models import CarMaker
from dashboard.models import CarModel
from dashboard.models import CarBodyStyle
from dashboard.models import CarListing
import flask_sqlalchemy


def render_template_app(*args, **kwargs):
    """ Overloads render template so to include data that should be used on all templates"""
    if current_app.config['SQLALCHEMY_RECORD_QUERIES']:
        queries = flask_sqlalchemy.get_debug_queries()
        kwargs['queries'] = queries
    return render_template(*args, **kwargs)


def add_filters(query, args=None):
    """ Add filter queries to data display"""
    form_data = dict()
    form_data['makers'] = [x[0] for x in
                           db.session.query(CarMaker.maker_name).distinct().order_by(CarMaker.maker_name).all()]
    form_data['models'] = [x[0] for x in
                           db.session.query(CarModel.model_name).distinct().order_by(CarModel.model_name).all()]
    form_data['styles'] = \
        [x[0] for x in db.session.query(CarBodyStyle.bodystyle_name).distinct().order_by(
            CarBodyStyle.bodystyle_name).all()]
    form_data['years'] = [x[0] for x in
                          db.session.query(CarListing.year_car).distinct().order_by(db.desc(CarListing.year_car)).all()]

    filters = dict()
    if args:
        maker = args.get('maker', default=None)
        model = args.get('model', default=None)
        if maker and (maker in form_data['makers']):
            query = query.filter(CarMaker.maker_name == maker)
            filters['maker'] = maker

            # adjust models according to maker selection
            form_data['models'] = [x[0] for x in
                                   db.session.query(CarModel.model_name).
                                   join(CarMaker, CarMaker.maker_id == CarModel.maker_id).
                                   filter(CarMaker.maker_name == maker).
                                   distinct().order_by(CarModel.model_name).all()]

            if model:
                if model in form_data['models']:
                    query = query.filter(CarModel.model_name == model)
                    filters['model'] = model
                else:
                    filters['model'] = None

        else:
            filters['maker'] = None
            if model and (model in form_data['models']):
                query = query.filter(CarModel.model_name == model)
                filters['model'] = model
            else:
                filters['model'] = None

        style = args.get('style', default=None)
        if style and (style in form_data['styles']):
            query = query.filter(CarBodyStyle.bodystyle_name == style)
            filters['style'] = style
        else:
            filters['style'] = None

        year = args.get('year', default=None, type=int)
        if year and (year in form_data['years']):
            query = query.filter(CarListing.year_car == year)
            filters['year'] = year
        else:
            filters['year'] = None

    return query, filters, form_data
