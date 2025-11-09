from flask import Blueprint, render_template

webui_bp = Blueprint("webui", __name__)

@webui_bp.route("/")
def dashboard():
    return render_template("dashboard.html")
