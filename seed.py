from app import app
from models import db
from models.crop import Crop

with app.app_context():

    if Crop.query.count() == 0:

        db.session.add_all([

            Crop(
                name="Carrot",
                buy_price=5,
                sell_price=10,
                grow_time=90,
                sprite_sheet="carrot",
                stages=4
            ),

            Crop(
                name="Potato",
                buy_price=10,
                sell_price=18,
                grow_time=180,
                sprite_sheet="potato",
                stages=4
            ),

            Crop(
                name="Corn",
                buy_price=20,
                sell_price=35,
                grow_time=300,
                sprite_sheet="corn",
                stages=4
            )

        ])

        db.session.commit()

        print("Crops seeded successfully!")

    else:

        print("Crops already exist.")