from flask import Blueprint
from flask import redirect
from flask import request
from flask import flash
from flask import url_for
from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user
from dashboard import db
from dashboard import bcrypt
from dashboard.hcs.utils import render_template_app
from dashboard.models import User
from dashboard.users.forms import LoginForm
from dashboard.users.forms import RegistrationForm
from dashboard.users.forms import UpdateProfileForm

users = Blueprint('users', __name__)


@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('hcs.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'You are logged in as {form.email.data}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('hcs.home'))
        else:
            flash('Login Error: Please check email and password', 'danger')
    return render_template_app('login.html', login_form=form)


@users.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('User logout completed')
    return redirect(url_for('hcs.home'))


@users.route("/registration", methods=['GET', 'POST'])
def registration():
    if current_user.is_authenticated:
        return redirect(url_for('hcs.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created, you can now login')
        return redirect(url_for('users.login'))

    return render_template_app('registration.html', form=form)


@users.route("/profile", methods=['GET', 'POST'])
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='images/' + current_user.image_src)
    return render_template_app('profile.html',
                               title='Profile',
                               image_file=image_file,
                               form=form)
