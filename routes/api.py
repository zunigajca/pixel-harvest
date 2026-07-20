from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import func

from models import db
from models.plot import Plot
from models.crop import Crop

api_bp = Blueprint("api", __name__, url_prefix="/api")

CROP_TIERS = {"Carrot": 1, "Potato": 2, "Corn": 3}


def sell_value(crop):
    return int(crop.sell_price * (1 + .25 * (current_user.seed_tier - 1)))


def plot_payload(plot):
    return {
        "plot_id": plot.id,
        "state": plot.state,
        "crop": plot.crop.name if plot.crop else None,
        "stage": plot.stage,
        "is_ready": plot.is_ready,
    }


def player_payload():
    return {
        "gold": current_user.gold,
        "plot_level": current_user.plot_level,
        "seed_tier": current_user.seed_tier,
        "farmkeeper_level": current_user.farmkeeper_level,
        "plot_cost": 100 * current_user.plot_level,
        "seed_cost": 125 * current_user.seed_tier if current_user.seed_tier < 3 else None,
        "farmkeeper_cost": 350 if not current_user.farmkeeper_level else None,
    }


@api_bp.route("/farm")
@login_required
def farm():
    plots = (Plot.query.filter_by(user_id=current_user.id)
             .order_by(Plot.position).all())
    crops = Crop.query.order_by(Crop.buy_price).all()
    return jsonify({"success": True, **player_payload(),
                    "plots": [plot_payload(plot) for plot in plots],
                    "crops": [{"id": crop.id, "name": crop.name, "buy_price": crop.buy_price,
                               "sell_price": sell_value(crop), "grow_time": crop.grow_time,
                               "tier": CROP_TIERS.get(crop.name, 1),
                               "unlocked": CROP_TIERS.get(crop.name, 1) <= current_user.seed_tier} for crop in crops]})


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

    if CROP_TIERS.get(crop.name, 1) > current_user.seed_tier:
        return jsonify({"success": False, "error": "Upgrade your seeds to unlock this crop."}), 400

    if current_user.gold < crop.buy_price:
        return jsonify({"success": False, "error": "Not enough gold"}), 400

    current_user.gold -= crop.buy_price

    plot.crop = crop
    plot.planted_at = datetime.now(timezone.utc)
    plot.state = "PLANTED"

    db.session.commit()

    return jsonify({"success": True, **player_payload(), **plot_payload(plot)})


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

    current_user.gold += sell_value(plot.crop)

    plot.crop = None
    plot.crop_id = None
    plot.planted_at = None
    plot.watered_at = None
    plot.state = "EMPTY"

    db.session.commit()

    return jsonify({"success": True, **player_payload(), **plot_payload(plot)})


@api_bp.route("/upgrade", methods=["POST"])
@login_required
def upgrade():
    action = (request.get_json() or {}).get("action")
    if action == "plots":
        cost = 100 * current_user.plot_level
        if current_user.gold < cost:
            return jsonify({"success": False, "error": "Not enough gold for more plots."}), 400
        last_position = db.session.query(func.max(Plot.position)).filter_by(user_id=current_user.id).scalar() or -1
        current_user.gold -= cost
        current_user.plot_level += 1
        db.session.add_all(Plot(user_id=current_user.id, position=last_position + number, state="EMPTY") for number in range(1, 5))
        message = "Four new plots are ready!"
    elif action == "seeds":
        if current_user.seed_tier >= 3:
            return jsonify({"success": False, "error": "Your seeds are already master grade."}), 400
        cost = 125 * current_user.seed_tier
        if current_user.gold < cost:
            return jsonify({"success": False, "error": "Not enough gold for a seed upgrade."}), 400
        current_user.gold -= cost
        current_user.seed_tier += 1
        message = "Seed tier upgraded! New crops may be available."
    elif action == "farmkeeper":
        if current_user.farmkeeper_level:
            return jsonify({"success": False, "error": "Your farm keeper is already working."}), 400
        if current_user.gold < 350:
            return jsonify({"success": False, "error": "Not enough gold to hire the farm keeper."}), 400
        current_user.gold -= 350
        current_user.farmkeeper_level = 1
        message = "Farm keeper hired! They will harvest and replant for you."
    else:
        return jsonify({"success": False, "error": "Unknown upgrade."}), 400
    db.session.commit()
    return jsonify({"success": True, "message": message, **player_payload()})


@api_bp.route("/idle-tick", methods=["POST"])
@login_required
def idle_tick():
    if not current_user.farmkeeper_level:
        return jsonify({"success": True, "worked": 0, **player_payload()})
    worked = 0
    ready_plots = Plot.query.filter_by(user_id=current_user.id, state="PLANTED").all()
    for plot in ready_plots:
        if not plot.is_ready:
            continue
        crop = plot.crop
        current_user.gold += sell_value(crop)
        if current_user.gold >= crop.buy_price:
            current_user.gold -= crop.buy_price
            plot.planted_at = datetime.now(timezone.utc)
            plot.state = "PLANTED"
        else:
            plot.crop = None
            plot.crop_id = None
            plot.planted_at = None
            plot.state = "EMPTY"
        worked += 1
    if worked:
        db.session.commit()
    return jsonify({"success": True, "worked": worked, **player_payload(),
                    "plots": [plot_payload(plot) for plot in ready_plots]})
