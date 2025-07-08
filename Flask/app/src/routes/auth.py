from flask import Blueprint, render_template, redirect, request, url_for, session, flash, jsonify, current_app
import app.config as config



auth = Blueprint('auth', __name__)

# Hardcoded credentials
users = {
    'email': config.ADMIN_EMAIL,
    'password': config.ADMIN_PASSWORD

}

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        print(email, password)
        print(users)

        if users.get('email') == email and  users.get('password') == password:
            session['user'] = users
            flash('Login successful', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('pages/auth/login.html')

@auth.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('auth.login'))

