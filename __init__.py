import os

from flask import Flask, render_template
from flask_mysqldb import MySQL
from flask_login import LoginManager
def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = '123456'
    app.config['MYSQL_DB'] = 'project'
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from . import db
    db.init_app(app)
    from .auth import create_auth_blueprint
    auth_bp = create_auth_blueprint(login_manager)
    app.register_blueprint(auth_bp)
    # app.add_url_rule('/', endpoint='auth.login')

    #  a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    @app.route('/')
    def home():
        return render_template('base.html')

    return app