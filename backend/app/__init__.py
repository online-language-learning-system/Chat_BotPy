from __future__ import annotations

from flask import Flask
from flasgger import Swagger
from flask_pymongo import PyMongo
from .config import settings

mongo = PyMongo()

def create_app() -> Flask:
    app = Flask(__name__)
    app.config [ 'MONGO_URI' ] = settings.MONGODB_URI
    mongo.init_app(app) # khởi tạo instance của PyMongo chưa trong biến mongo theo config app
    Swagger_template = {
        'info': {
            'title': settings.APP_NAME,
            'description': 'Chat Bot',
            'version': settings.APP_VERSION,
        },
        'basepath': '/',
        'schemes': ['http'],
    }
    Swagger(app, template=Swagger_template)
    
    from .routes import init_routes
    init_routes(app)
    
    return app