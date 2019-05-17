from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from dashboard.config import Config

# Create extension without binding application . Binding happen inside factory
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'


def create_app(configuration=Config):
    app = Flask(__name__)
    app.config.from_object(configuration)

    with app.app_context():
        db.init_app(app)
        bcrypt.init_app(app)
        login_manager.init_app(app)

        # routes must be imported after db initialization
        from dashboard import routes

        # import and register blueprints
        from dashboard.users.routes import users
        app.register_blueprint(users, url_prefix='/hcs/users')
        from dashboard.errors.handlers import errors
        app.register_blueprint(errors)
        from dashboard.api.api import api_bp
        app.register_blueprint(api_bp)
        from dashboard.hcs.routes import hcs
        app.register_blueprint(hcs, url_prefix='/hcs')
        # Main landing page, not necessary for HCS Dashboard
        # Dashboard URL is domain.com/hcs/....
        try:
            from dashboard.main.routes import main
            app.register_blueprint(main)
        except ModuleNotFoundError:
            pass

    return app




