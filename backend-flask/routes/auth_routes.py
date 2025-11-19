from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt, datetime
from models import db, User
import re
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/auth")

# ✅ Register Route - ADMIN ONLY
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    phone = data.get("phone", "").strip()
    # ✅ FORCE ADMIN ROLE - Remove role parameter, always create admin
    role = "admin"

    # ✅ Field validation
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not email:
        return jsonify({"error": "Email is required"}), 400
    if not password:
        return jsonify({"error": "Password is required"}), 400
    if not phone:
        return jsonify({"error": "Phone number is required"}), 400

    # ✅ Email format validation
    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(email_pattern, email):
        return jsonify({"error": "Invalid email format. Please enter a valid email address."}), 400

    # ✅ Password strength validation
    if len(password) < 6 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return jsonify({
            "error": "Password must be at least 6 characters long and include both letters and numbers"
        }), 400

    # ✅ Case-sensitive duplicate check
    existing_email = User.query.filter(User.email == email).first()
    if existing_email:
        return jsonify({"error": "Email already registered. Please use a different email."}), 400

    existing_phone = User.query.filter(User.phone == phone).first()
    if existing_phone:
        return jsonify({"error": "Phone number already registered. Please use a different number."}), 400

    # ✅ Save new admin user with IntegrityError handling
    try:
        hashed_pw = generate_password_hash(password)
        new_user = User(
            name=name,
            email=email,
            password=hashed_pw,
            role=role,
            phone=phone,
            is_active=True
        )
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({"message": f"Admin account registered successfully! You can now login."}), 201
    except IntegrityError as e:
        db.session.rollback()
        error_str = str(e)
        if 'email' in error_str.lower() or 'unique constraint' in error_str.lower():
            if 'phone' in error_str.lower():
                return jsonify({"error": "Both email and phone already registered"}), 400
            return jsonify({"error": "Email already registered"}), 400
        elif 'phone' in error_str.lower():
            return jsonify({"error": "Phone number already registered"}), 400
        else:
            return jsonify({"error": "Registration failed: Duplicate entry"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

# ✅ Login Route - ADMIN ONLY
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({"error": "Invalid JSON", "details": str(e)}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401
    
    # ✅ CHECK IF USER IS ADMIN - ONLY ADMINS CAN LOGIN
    if user.role != 'admin':
        return jsonify({"error": "Access denied. Only administrators can login to this system."}), 403
    
    if not user.is_active:
        return jsonify({"error": "Your account is not active. Please contact the system administrator.", "is_active": False}), 403

    if not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    SECRET_KEY = current_app.config['JWT_SECRET_KEY']
    token = jwt.encode(
        {
            "id": user.id,
            "role": user.role,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12),
        },
        SECRET_KEY,
        algorithm="HS256",
    )

    # ✅ UNIFIED RESPONSE - ADMIN ONLY
    return jsonify({
        "message": "Login successful",
        "token": token,
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "phone": user.phone,
        "is_active": user.is_active
    }), 200

# ✅ Token verification decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'error': 'Token is missing!'}), 401

        SECRET_KEY = current_app.config['JWT_SECRET_KEY']

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.get(data['id'])
            if not current_user:
                return jsonify({'error': 'User not found!'}), 404
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

# ✅ Admin required decorator - ADD THIS
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'error': 'Token is missing!'}), 401

        SECRET_KEY = current_app.config['JWT_SECRET_KEY']

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.get(data['id'])
            if not current_user:
                return jsonify({'error': 'User not found!'}), 404
            
            # ✅ CHECK IF USER IS ADMIN
            if current_user.role != 'admin':
                return jsonify({'error': 'Admin access required!'}), 403
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated


# ✅ Profile route (Protected)
@auth_bp.route("/profile", methods=["GET"])
@token_required
def profile(current_user):
    return jsonify({
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active
    }), 200




# ---------------------------
# Admin: users list + search - ADD @admin_required
# ---------------------------
@auth_bp.route("/users", methods=["GET"])
@admin_required  # ✅ ADD THIS
def get_users(current_user):
    """
    GET /auth/users?q=searchTerm
    If q not provided -> return all users
    """
    q = request.args.get("q", "").strip()
    if q:
        # MySQL case-insensitive search using LIKE
        search_pattern = f"%{q}%"
        conditions = [
            User.name.like(search_pattern),
            User.email.like(search_pattern),
            User.phone.like(search_pattern)
        ]
        # Add ID search if q is a digit
        if q.isdigit():
            conditions.append(User.id == int(q))
        
        users = User.query.filter(or_(*conditions)).all()
    else:
        users = User.query.order_by(User.id.desc()).all()

    result = []
    for u in users:
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "phone": u.phone,
            "role": u.role,
            "is_active": bool(u.is_active),
            "created_at": u.created_at.isoformat() if u.created_at else None
        })

    return jsonify(result), 200


# ---------------------------
# Admin: create user (add) - ADD @admin_required
# ---------------------------
@auth_bp.route("/users", methods=["POST"])
@admin_required  # ✅ ADD THIS
def create_user(current_user):
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    role = data.get("role", "user")
    password = data.get("password")

    # validation
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not email:
        return jsonify({"error": "Email is required"}), 400
    if not phone:
        return jsonify({"error": "Phone is required"}), 400
    if not password:
        return jsonify({"error": "Password is required"}), 400

    # duplicates (case-sensitive per your request)
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400
    if User.query.filter_by(phone=phone).first():
        return jsonify({"error": "Phone already registered"}), 400

    # ✅ Add IntegrityError handling
    try:
        hashed_pw = generate_password_hash(password)
        new_user = User(name=name, email=email, phone=phone, role=role, password=hashed_pw, is_active=True)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({"message": "User created", "id": new_user.id}), 201
    except IntegrityError as e:
        db.session.rollback()
        error_str = str(e)
        if 'email' in error_str.lower() or 'unique constraint' in error_str.lower():
            if 'phone' in error_str.lower():
                return jsonify({"error": "Both email and phone already registered"}), 400
            return jsonify({"error": "Email already registered"}), 400
        elif 'phone' in error_str.lower():
            return jsonify({"error": "Phone number already registered"}), 400
        else:
            return jsonify({"error": "Duplicate entry detected"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"User creation failed: {str(e)}"}), 500


# ---------------------------
# Admin: update user - ADD @admin_required
# ---------------------------
@auth_bp.route("/users/<int:user_id>", methods=["PUT"])
@admin_required  # ✅ ADD THIS
def update_user(current_user, user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}
    name = data.get("name", user.name).strip()
    email = data.get("email", user.email).strip()
    phone = data.get("phone", user.phone).strip()
    role = data.get("role", user.role)
    password = data.get("password", None)  # optional

    # If changing email/phone, ensure not colliding with other users
    other = User.query.filter(User.email == email, User.id != user.id).first()
    if other:
        return jsonify({"error": "Email already used by another user"}), 400
    other_phone = User.query.filter(User.phone == phone, User.id != user.id).first()
    if other_phone:
        return jsonify({"error": "Phone already used by another user"}), 400

    user.name = name
    user.email = email
    user.phone = phone
    user.role = role

    if password:
        user.password = generate_password_hash(password)

    db.session.commit()
    return jsonify({"message": "User updated"}), 200


# ---------------------------
# Admin: delete user - ADD @admin_required
# ---------------------------
@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required  # ✅ ADD THIS
def delete_user(current_user, user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        print(f"✅ User {user_id} deleted successfully by admin {current_user.id}")
        return jsonify({"message": "User deleted successfully ✅"}), 200
    except IntegrityError as e:
        db.session.rollback()
        print(f"❌ IntegrityError in delete: {str(e)}")
        return jsonify({"error": "Cannot delete user: integrity constraint violation"}), 400
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in delete: {str(e)}")
        return jsonify({"error": f"Delete failed: {str(e)}"}), 500



# ---------------------------
# Admin: toggle active/inactive - ADD @admin_required
# ---------------------------
@auth_bp.route("/users/<int:user_id>/toggle", methods=["PATCH"])
@admin_required  # ✅ ADD THIS
def toggle_user(current_user, user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    user.is_active = not bool(user.is_active)
    db.session.commit()
    return jsonify({"message": "Status updated", "is_active": bool(user.is_active)}), 200
# ---------------------------------------------------------------------------------------

@auth_bp.route("/update-profile", methods=["PUT"])
@token_required
def update_profile(current_user):
    data = request.get_json() or {}
    name = data.get("name", current_user.name).strip()
    phone = data.get("phone", current_user.phone).strip()
    password = data.get("password")

    # check duplicates
    other_phone = User.query.filter(User.phone == phone, User.id != current_user.id).first()
    if other_phone:
        return jsonify({"error": "Phone number already used"}), 400

    current_user.name = name
    current_user.phone = phone
    if password:
        current_user.password = generate_password_hash(password)

    db.session.commit()
    return jsonify({"message": "Profile updated successfully ✅"}), 200

# ✅ Fetch single user details by ID
@auth_bp.route("/user/<int:user_id>", methods=["GET"])
def get_user_by_id(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": bool(user.is_active)
    }), 200
