from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

from config import Config
from models import db
from models.user import User

load_dotenv()

login_manager = LoginManager()
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)

    from routes.auth import auth_bp
    from routes.game import game_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)