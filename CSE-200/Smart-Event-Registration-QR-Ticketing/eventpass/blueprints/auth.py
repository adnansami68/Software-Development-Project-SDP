from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from ..models import User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email, is_active=True).first()
        if user and user.check_password(password):
            login_user(user, remember=request.form.get("remember") == "on")
            flash("Welcome back. You are signed in.", "success")
            return redirect(url_for("admin.dashboard"))
        flash("The email or password is incorrect.", "danger")

    return render_template("auth/login.html")


@auth_bp.post("/logout")
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("public.index"))
