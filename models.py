from flask_sqlalchemy import SQLAlchemy
from peewee import *
import os

# db=SqliteDatabase("data.db")

# db = PostgresqlDatabase(
#     os.getenv('DB_NAME'),
#     user=os.getenv('DB_USER'),
#     password=os.getenv('DB_PASSWORD'),
#     host=os.getenv('DB_HOST'),
#     port=os.getenv('DB_PORT')
# )

db = PostgresqlDatabase(os.getenv('DB_NAME'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'))

class Products(db.Model):
    __tablename__ = "product"

    id = AutoField(primary_key=True, default=0)
    # id = db.Column(db.Integer, primary_key=True)
    name = (CharField(default=""))
    type = (CharField(default=""))
    description = (CharField(default=""))
    image = (CharField(default=""))
    height = (FloatField(default=0))
    weight = (FloatField(default=0))
    price = (FloatField(default=0))
    in_stock = (BooleanField(default=0))

 
    def __repr__(self):
        return f"{self.name}:{self.id}"

class Order(db.Model):
    __tablename__ = "order"
 
    id = AutoField(primary_key=True)
    total_price = (FloatField(default=0))
    shipping_price = (FloatField(default=0))
    paid = (BooleanField(default=0))
    being_paid = (BooleanField(default=0))
    email = (CharField(default=""))
    transaction = (CharField(default=""))
    credit_card = (CharField(default=""))
    product = (CharField(default=""))
    shipping_information = (CharField(default=""))

    def __repr__(self):
        return f"{self.product}:{self.id}"