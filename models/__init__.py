from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Register all models
from .user import User
from .plot import Plot
from .crop import Crop