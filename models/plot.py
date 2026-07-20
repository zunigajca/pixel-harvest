from datetime import datetime, timezone

from models import db


class Plot(db.Model):
    __tablename__ = "plots"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    position = db.Column(db.Integer, nullable=False)

    crop_id = db.Column(
        db.Integer,
        db.ForeignKey("crops.id"),
        nullable=True
    )

    state = db.Column(
        db.String(20),
        default="EMPTY",
        nullable=False
    )

    planted_at = db.Column(db.DateTime, nullable=True)

    watered_at = db.Column(db.DateTime, nullable=True)

    crop = db.relationship("Crop", backref="plots")

    @property
    def stage(self):
        """Returns the current crop stage."""

        if self.state == "EMPTY":
            return None

        if not self.crop or not self.planted_at:
            return None

        elapsed = (
            datetime.now(timezone.utc)
            - self.planted_at.replace(tzinfo=timezone.utc)
        ).total_seconds()

        progress = elapsed / self.crop.grow_time

        stage = int(progress * self.crop.stages)

        return min(stage, self.crop.stages - 1)

    @property
    def is_ready(self):
        """Returns True when the crop can be harvested."""

        if self.state != "PLANTED":
            return False

        if not self.crop or not self.planted_at:
            return False

        elapsed = (
            datetime.now(timezone.utc)
            - self.planted_at.replace(tzinfo=timezone.utc)
        ).total_seconds()

        return elapsed >= self.crop.grow_time