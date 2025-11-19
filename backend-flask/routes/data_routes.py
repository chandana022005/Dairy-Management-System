from flask import Blueprint, request, jsonify
from models import db, Customer, MilkCollection, Payment
from routes.auth_routes import token_required

data_bp = Blueprint("data_bp", __name__)

# ---------------- CUSTOMER ROUTES ---------------- #

@data_bp.route("/customers", methods=["POST"])
@token_required
def add_customer(current_user):
    data = request.get_json()
    new_customer = Customer(
        name=data.get("name"),
        phone=data.get("phone"),
        address=data.get("address"),
        user_id=current_user.id
    )
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({"message": "Customer added successfully"}), 201


@data_bp.route("/customers", methods=["GET"])
@token_required
def get_customers(current_user):
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    result = [
        {"id": c.id, "name": c.name, "phone": c.phone, "address": c.address}
        for c in customers
    ]
    return jsonify(result)


@data_bp.route("/customers/<int:id>", methods=["PUT"])
@token_required
def update_customer(current_user, id):
    customer = Customer.query.filter_by(id=id, user_id=current_user.id).first()
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    data = request.get_json()
    customer.name = data.get("name", customer.name)
    customer.phone = data.get("phone", customer.phone)
    customer.address = data.get("address", customer.address)

    db.session.commit()
    return jsonify({"message": "Customer updated successfully"})


@data_bp.route("/customers/<int:id>", methods=["DELETE"])
@token_required
def delete_customer(current_user, id):
    customer = Customer.query.filter_by(id=id, user_id=current_user.id).first()
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted successfully"})


# ---------------- MILK COLLECTION ROUTES ---------------- #

@data_bp.route("/milk", methods=["POST"])
@token_required
def add_milk_record(current_user):
    data = request.get_json()
    new_record = MilkCollection(
        customer_id=data.get("customer_id"),
        date=data.get("date"),
        quantity=data.get("quantity"),
        fat=data.get("fat"),
        price_per_litre=data.get("price_per_litre"),
        total_price=data.get("total_price")
    )
    db.session.add(new_record)
    db.session.commit()
    return jsonify({"message": "Milk record added successfully"}), 201


@data_bp.route("/milk", methods=["GET"])
@token_required
def get_milk_records(current_user):
    records = (
        db.session.query(MilkCollection)
        .join(Customer)
        .filter(Customer.user_id == current_user.id)
        .all()
    )
    result = [
        {
            "id": r.id,
            "customer_id": r.customer_id,
            "date": r.date,
            "quantity": r.quantity,
            "fat": r.fat,
            "price_per_litre": r.price_per_litre,
            "total_price": r.total_price
        }
        for r in records
    ]
    return jsonify(result)


@data_bp.route("/milk/<int:id>", methods=["PUT"])
@token_required
def update_milk_record(current_user, id):
    record = db.session.query(MilkCollection).join(Customer).filter(
        MilkCollection.id == id,
        Customer.user_id == current_user.id
    ).first()
    if not record:
        return jsonify({"error": "Milk record not found"}), 404

    data = request.get_json()
    record.quantity = data.get("quantity", record.quantity)
    record.fat = data.get("fat", record.fat)
    record.price_per_litre = data.get("price_per_litre", record.price_per_litre)
    record.total_price = data.get("total_price", record.total_price)
    record.date = data.get("date", record.date)

    db.session.commit()
    return jsonify({"message": "Milk record updated successfully"})


@data_bp.route("/milk/<int:id>", methods=["DELETE"])
@token_required
def delete_milk_record(current_user, id):
    record = db.session.query(MilkCollection).join(Customer).filter(
        MilkCollection.id == id,
        Customer.user_id == current_user.id
    ).first()
    if not record:
        return jsonify({"error": "Milk record not found"}), 404

    db.session.delete(record)
    db.session.commit()
    return jsonify({"message": "Milk record deleted successfully"})


# ---------------- PAYMENT ROUTES ---------------- #

@data_bp.route("/payments", methods=["POST"])
@token_required
def add_payment(current_user):
    data = request.get_json()
    new_payment = Payment(
        customer_id=data.get("customer_id"),
        amount_paid=data.get("amount_paid"),
        date=data.get("date"),
        payment_mode=data.get("payment_mode")
    )
    db.session.add(new_payment)
    db.session.commit()
    return jsonify({"message": "Payment added successfully"}), 201


@data_bp.route("/payments", methods=["GET"])
@token_required
def get_payments(current_user):
    payments = (
        db.session.query(Payment)
        .join(Customer)
        .filter(Customer.user_id == current_user.id)
        .all()
    )
    result = [
        {
            "id": p.id,
            "customer_id": p.customer_id,
            "amount_paid": p.amount_paid,
            "date": p.date,
            "payment_mode": p.payment_mode
        }
        for p in payments
    ]
    return jsonify(result)


@data_bp.route("/payments/<int:id>", methods=["PUT"])
@token_required
def update_payment(current_user, id):
    payment = db.session.query(Payment).join(Customer).filter(
        Payment.id == id,
        Customer.user_id == current_user.id
    ).first()
    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    data = request.get_json()
    payment.amount_paid = data.get("amount_paid", payment.amount_paid)
    payment.date = data.get("date", payment.date)
    payment.payment_mode = data.get("payment_mode", payment.payment_mode)

    db.session.commit()
    return jsonify({"message": "Payment updated successfully"})


@data_bp.route("/payments/<int:id>", methods=["DELETE"])
@token_required
def delete_payment(current_user, id):
    payment = db.session.query(Payment).join(Customer).filter(
        Payment.id == id,
        Customer.user_id == current_user.id
    ).first()
    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    db.session.delete(payment)
    db.session.commit()
    return jsonify({"message": "Payment deleted successfully"})
