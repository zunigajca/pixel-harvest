from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from models import db
from models.plot import Plot
from models.crop import Crop

api_bp = Blueprint("api", __name__, url_prefix="/api")


def plot_payload(plot):
    return {
        "plot_id": plot.id,
        "state": plot.state,
        "crop": plot.crop.name if plot.crop else None,
        "stage": plot.stage,
        "is_ready": plot.is_ready,
    }


@api_bp.route("/farm")
@login_required
def farm():
    plots = (Plot.query.filter_by(user_id=current_user.id)
             .order_by(Plot.position).all())
    return jsonify({"success": True, "gold": current_user.gold,
                    "plots": [plot_payload(plot) for plot in plots]})


@api_bp.route("/plant", methods=["POST"])
@login_required
def plant():

    data = request.get_json()

    plot_id = data.get("plot_id")
    crop_id = data.get("crop_id")

    plot = Plot.query.get_or_404(plot_id)

    if plot.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    if plot.state != "EMPTY":
        return jsonify({"success": False, "error": "Plot already occupied"}), 400

    crop = Crop.query.get_or_404(crop_id)

    if current_user.gold < crop.buy_price:
        return jsonify({"success": False, "error": "Not enough gold"}), 400

    current_user.gold -= crop.buy_price

    plot.crop = crop
    plot.planted_at = datetime.now(timezone.utc)
    plot.state = "PLANTED"

    db.session.commit()

    return jsonify({"success": True, "gold": current_user.gold, **plot_payload(plot)})


@api_bp.route("/harvest", methods=["POST"])
@login_required
def harvest():

    data = request.get_json()

    plot_id = data.get("plot_id")

    plot = Plot.query.get_or_404(plot_id)

    if plot.user_id != current_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    if not plot.is_ready:
        return jsonify({"success": False, "error": "Crop is not ready"}), 400

    current_user.gold += plot.crop.sell_price

    plot.crop = None
    plot.crop_id = None
    plot.planted_at = None
    plot.watered_at = None
    plot.state = "EMPTY"

    db.session.commit()

    return jsonify({"success": True, "gold": current_user.gold, **plot_payload(plot)})
