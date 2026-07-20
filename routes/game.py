from flask import Blueprint, render_template
from flask_login import login_required, current_user

from models.plot import Plot
from models.crop import Crop

game_bp = Blueprint("game", __name__)


@game_bp.route("/")
def home():
    return render_template("index.html")


@game_bp.route("/dashboard")
@login_required
def dashboard():

    plots = (
        Plot.query
        .filter_by(user_id=current_user.id)
        .order_by(Plot.position)
        .all()
    )

    return render_template(
        "dashboard.html",
        plots=plots,
        carrot=Crop.query.filter_by(name="Carrot").first()
    )
