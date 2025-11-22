def init_routes(app):
    from .conversation_routes import bp as conv_bp

    app.register_blueprint(conv_bp,url_prefix='/api/conversation') # đăng ký route conversation ở địa chỉ /api/conversation
