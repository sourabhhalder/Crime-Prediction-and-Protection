from flask import Flask, render_template

# DB
from models.db import init_db

# Blueprints
from routes.auth import auth_bp
from routes.predict import predict_bp

# -------------------------------
# CREATE APP
# -------------------------------
app = Flask(__name__)

# Secret key for sessions (login)
app.secret_key = "supersecretkey123"

# -------------------------------
# INIT DATABASE
# -------------------------------
init_db()

# -------------------------------
# REGISTER BLUEPRINTS
# -------------------------------
app.register_blueprint(auth_bp)
app.register_blueprint(predict_bp)

# -------------------------------
# HOME ROUTE
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)