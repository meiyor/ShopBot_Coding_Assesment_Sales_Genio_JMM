from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ShopData(db.Model):

    id = db.Column(db.Integer, primary_key=True, index=True)
    code = db.Column(db.String)
    date = db.Column(db.String)
    username = db.Column(db.String)
    Interaction = db.Column(db.String)

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f'<chatbot {self.firstname}>'


class ShopData_Product(db.Model):

    id = db.Column(db.Integer, primary_key=True, index=True)
    code = db.Column(db.String)
    date = db.Column(db.String)
    username = db.Column(db.String)
    product_name = db.Column(db.String)
    price = db.Column(db.String)
    description = db.Column(db.String)
    stock_availability = db.Column(db.String)

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f'<chatbot {self.firstname}>'
