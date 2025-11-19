from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import timedelta
from models import db
from routes.auth_routes import auth_bp
from routes.data_routes import data_bp
from dotenv import load_dotenv
load_dotenv()
from routes.chatbot_routes import chatbot_bp



app = Flask(__name__)

# ✅ CORS Configuration - Allow all origins for production
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False
    }
})

# ✅ Database config
# Railway cloud database (production)
import os
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:BEOJvNkZitaZYrqpmEdCZzainncEhAcl@turntable.proxy.rlwy.net:22022/railway')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Add connection pool settings to prevent timeouts
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Test connections before using
    'pool_recycle': 300,     # Recycle connections after 5 minutes
    'connect_args': {
        'connect_timeout': 10  # 10 second connection timeout
    }
}

# ✅ JWT config
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
app.secret_key = 'your_secret_key_here'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# ✅ Initialize extensions
db.init_app(app)

# ✅ Create tables if not exist
with app.app_context():
    db.create_all()

# ✅ Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(data_bp)
app.register_blueprint(chatbot_bp, url_prefix='/chat')

@app.route("/")
def home():
    return jsonify({"message": "Dairy Management Backend is running!"})

if __name__ == "__main__":
    # Bind to 0.0.0.0 so physical devices on the LAN can reach the dev server.
    # Development only — be careful exposing this on untrusted networks.
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
