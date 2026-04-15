from flask import Blueprint, request, jsonify, session, render_template

from models.db import add_user, validate_user

auth_bp = Blueprint("auth", __name__)

# -------------------------------
# PAGE ROUTES
# -------------------------------
@auth_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


@auth_bp.route("/signup", methods=["GET"])
def signup_page():
    return render_template("signup.html")


# 🔥 NEW: PROFILE PAGE
@auth_bp.route("/profile", methods=["GET"])
def profile_page():
    return render_template("profile.html")


# 🔥 NEW: DASHBOARD PAGE
@auth_bp.route("/dashboard", methods=["GET"])
def dashboard_page():
    return render_template("dashboard.html")


# -------------------------------
# SIGNUP API
# -------------------------------
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    try:
        add_user(name, email, password)
        return jsonify({"message": "User created successfully"})
    except Exception as e:
        print("Signup Error:", str(e))
        return jsonify({"error": "User already exists"}), 400


# -------------------------------
# LOGIN API
# -------------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = validate_user(email, password)

    if user:
        session["user"] = email
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"error": "Invalid credentials"}), 401


# -------------------------------
# LOGOUT
# -------------------------------
@auth_bp.route("/logout", methods=["GET"])
def logout():
    session.pop("user", None)
    return jsonify({"message": "Logged out"})