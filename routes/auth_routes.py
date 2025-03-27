from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from models import User
import os
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if user already exists
        db = g.db
        existing_user = db.users.find_one({'email': email})
        if existing_user:
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        # Create new user
        try:
            new_user = {
                'username': username,
                'email': email,
                'password_hash': generate_password_hash(password),
                'preferences': {
                    'default_market': 'NSE',
                    'notification_settings': {
                        'email_alerts': True,
                        'price_alerts': True,
                        'news_alerts': True
                    }
                },
                'watchlist': [],
                'created_at': datetime.now(),
                'last_login': datetime.now()
            }
            
            result = db.users.insert_one(new_user)
            new_user['_id'] = result.inserted_id
            
            # Create User object and log in
            user = User(new_user)
            login_user(user)
            
            flash('Registration successful! Welcome to Smart Financial Analyzer', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            flash('An error occurred during registration', 'danger')
            return render_template('register.html')
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required', 'danger')
            return render_template('login.html')
        
        # Find user
        db = g.db
        user_data = db.users.find_one({'email': email})
        
        if not user_data or not check_password_hash(user_data.get('password_hash', ''), password):
            flash('Invalid email or password', 'danger')
            return render_template('login.html')
        
        # Update last login
        db.users.update_one(
            {'_id': user_data['_id']},
            {'$set': {'last_login': datetime.now()}}
        )
        
        # Create User object and log in
        user = User(user_data)
        login_user(user)
        
        flash('Login successful!', 'success')
        
        # Redirect to the page user was trying to access or to dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('main.dashboard'))
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        default_market = request.form.get('default_market', 'NSE')
        email_alerts = 'email_alerts' in request.form
        price_alerts = 'price_alerts' in request.form
        news_alerts = 'news_alerts' in request.form
        
        # Validate input
        if not username or not email:
            flash('Username and email are required', 'danger')
            return redirect(url_for('auth.profile'))
        
        # Update user data
        db = g.db
        update_data = {
            'username': username,
            'email': email,
            'preferences.default_market': default_market,
            'preferences.notification_settings.email_alerts': email_alerts,
            'preferences.notification_settings.price_alerts': price_alerts,
            'preferences.notification_settings.news_alerts': news_alerts
        }
        
        db.users.update_one(
            {'_id': current_user.id},
            {'$set': update_data}
        )
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('profile.html')

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validate input
    if not current_password or not new_password or not confirm_password:
        flash('All password fields are required', 'danger')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('auth.profile'))
    
    # Verify current password
    db = g.db
    user_data = db.users.find_one({'_id': current_user.id})
    
    if not user_data or not check_password_hash(user_data.get('password_hash', ''), current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('auth.profile'))
    
    # Update password
    db.users.update_one(
        {'_id': current_user.id},
        {'$set': {'password_hash': generate_password_hash(new_password)}}
    )
    
    flash('Password updated successfully', 'success')
    return redirect(url_for('auth.profile'))

# Set up database reference
@auth_bp.before_request
def before_request():
    from app import db
    g.db = db
