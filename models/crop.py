from models import db


class Crop(db.Model):
    __tablename__ = "crops"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(30), unique=True, nullable=False)

    buy_price = db.Column(db.Integer, nullable=False)

    sell_price = db.Column(db.Integer, nullable=False)

    grow_time = db.Column(db.Integer, nullable=False)

    sprite_sheet = db.Column(db.String(100), nullable=False)

    stages = db.Column(db.Integer, default=4)