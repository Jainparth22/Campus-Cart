from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import Users
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

views = Blueprint('views', __name__)

@views.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html")

