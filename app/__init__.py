from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'construction-site-monitoring'
    
    socketio.init_app(app)
    
    from app.routes import main
    app.register_blueprint(main)
    
    return app 