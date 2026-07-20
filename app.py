from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

from config import Config
from models import db
from models.user import User
from models.crop import Crop

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
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(api_bp)

    @app.cli.command("init-game")
    def init_game():
        """Create the database tables and starter crop catalogue."""
        db.create_all()
        catalogue = [
            ("Carrot", 5, 10, 90, "carrot"),
            ("Potato", 12, 24, 150, "potato"),
            ("Corn", 25, 50, 240, "corn"),
        ]
        for name, buy, sell, growth, sprite in catalogue:
            if not Crop.query.filter_by(name=name).first():
                db.session.add(Crop(name=name, buy_price=buy, sell_price=sell,
                                    grow_time=growth, sprite_sheet=sprite, stages=4))
        if db.session.new:
            db.session.commit()
        print("Pixel Harvest is ready.")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
