from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import datetime
import os

app = Flask(__name__)
CORS(app)
@app.route("/")
def home():
    return {"status": "ERP Backend Running"}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///erp.db'
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# ---------------- MODELS ----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
@app.route("/create-admin")
def create_admin():
    with app.app_context():
        if not User.query.filter_by(username="admin").first():
            user = User(username="admin", password="1234")
            db.session.add(user)
            db.session.commit()
            return "Admin Created"
        return "Admin Already Exists"
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    phone = db.Column(db.String(20))
with app.app_context():
    db.create_all()
class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    rate = db.Column(db.Float)
    qty = db.Column(db.Float)
    unit = db.Column(db.String(10))

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(50))
    total = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# ---------------- ROUTES ----------------

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    user = User(username=data["username"], password=data["password"])
    db.session.add(user)
    db.session.commit()
    return {"msg": "User created"}

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username=data["username"], password=data["password"]).first()
    if not user:
        return {"msg": "Bad credentials"}, 401
    token = create_access_token(identity=user.username)
    return {"access_token": token}
@app.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    data = request.json
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    user = User.query.filter_by(username=get_jwt_identity()).first()

    if not user:
        return jsonify({"msg": "User not found"}), 404

    if user.password != current_password:
        return jsonify({"msg": "Current password incorrect"}), 400

    user.password = new_password
    db.session.commit()

    return jsonify({"msg": "Password updated successfully"})
@app.route("/add_stock", methods=["POST"])
@jwt_required()
def add_stock():
    data = request.json
    item = Stock(
        name=data["name"],
        rate=data["rate"],
        qty=data["qty"],
        unit=data["unit"]
    )
    db.session.add(item)
    db.session.commit()
    return {"msg": "Stock added"}

@app.route("/stock", methods=["GET"])
@jwt_required()
def get_stock():
    items = Stock.query.all()
    return jsonify([
        {"id": i.id, "name": i.name, "rate": i.rate, "qty": i.qty, "unit": i.unit}
        for i in items
    ])

@app.route("/create_sale", methods=["POST"])
@jwt_required()
def create_sale():
    data = request.json
    sale = Sale(invoice_no=data["invoice"], total=data["total"])
    db.session.add(sale)
    db.session.commit()
    return {"msg": "Sale saved"}

@app.route("/generate_invoice/<invoice>")
@jwt_required()
def generate_invoice(invoice):
    file_path = f"{invoice}.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Invoice No: " + invoice, styles['Normal']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Generated from ERP Web", styles['Normal']))

    doc.build(elements)
    return send_file(file_path, as_attachment=True)

# ---------------- RUN ----------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)





