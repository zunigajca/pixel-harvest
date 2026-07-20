from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from models import db
from models.user import User
from models.plot import Plot

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("game.dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("auth.register"))

        if not 3 <= len(username) <= 30 or not username.replace("_", "").isalnum():
            flash("Use 3–30 letters, numbers, or underscores for your username.", "danger")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("Your password must be at least 6 characters.", "danger")
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            flash("Username already exists.", "danger")
            return redirect(url_for("auth.register"))

        user = User(username=username)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Create a 4x4 starter farm
        starter_plots = [
            Plot(
                user_id=user.id,
                position=i,
                state="EMPTY"
            )
            for i in range(16)
        ]

        db.session.add_all(starter_plots)
        db.session.commit()

        flash("Account created successfully!", "success")

        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("game.dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(
            username=username
        ).first()

        if user and user.check_password(password):

            login_user(user)

            flash(f"Welcome back, {user.username}!", "success")

            return redirect(url_for("game.dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash("You have been logged out.", "info")

    return redirect(url_for("game.home"))
