from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from models import User, DailyTip
from app import db
import os
import json
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
        
        # Get personalization preferences
        experience_level = request.form.get('experience_level', 'Beginner')
        risk_profile = request.form.get('risk_profile', 'Moderate')
        daily_tip = 'daily_tip' in request.form
        dark_mode = 'dark_mode' in request.form
        skip_onboarding = 'skip_onboarding' in request.form
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if user already exists - email check
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered', 'danger')
            return render_template('register.html')
            
        # Check if username already exists
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash('Username already taken. Please choose a different username', 'danger')
            return render_template('register.html')
        
        # Create new user
        try:
            # Set user preferences with form values
            default_preferences = {
                "stock_watchlist": [],
                "favorite_sectors": [],
                "risk_profile": risk_profile,
                "investment_horizon": "Medium Term",
                "dark_mode": dark_mode,
                "daily_tip": daily_tip,
                "learning_notifications": True,
                "default_market": "NSE"
            }
            
            # Determine risk tolerance score based on risk profile
            risk_tolerance_score = 5  # Default moderate
            if risk_profile == "Conservative":
                risk_tolerance_score = 3
            elif risk_profile == "Aggressive":
                risk_tolerance_score = 8
                
            # Set default personal profile
            default_personal_profile = {
                "age_group": None,
                "income_bracket": None,
                "occupation": None,
                "industry": None,
                "location": None,
                "experience_level": experience_level,
                "financial_goals": [],
                "existing_investments": [],
                "monthly_expenses": None,
                "loan_emi": None,
                "risk_tolerance_score": risk_tolerance_score,
                "tax_bracket": None,
                "preferred_learning_style": "Text",
                "onboarding_completed": skip_onboarding  # Mark as completed if skipping
            }
            
            # Set learning progress based on experience level
            difficulty_level = "Beginner"
            learning_path = "Basics"
            
            if experience_level == "Intermediate":
                difficulty_level = "Intermediate"
                learning_path = "Intermediate"
            elif experience_level == "Advanced":
                difficulty_level = "Advanced"
                learning_path = "Advanced"
                
            default_learning_progress = {
                "completed_topics": [],
                "bookmarked_resources": [],
                "quiz_scores": {},
                "current_learning_path": learning_path,
                "difficulty_level": difficulty_level,
                "daily_quiz": True
            }
            
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                preferences=default_preferences,
                personal_profile=default_personal_profile,
                learning_progress=default_learning_progress
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            # Create a welcome tip
            welcome_tip = DailyTip(
                user_id=new_user.id,
                tip_title="Welcome to Smart Financial Analyzer",
                tip_text="Start by exploring the dashboard or setting up your personal profile to get more personalized financial advice.",
                tip_category="welcome",
                is_personalized=True
            )
            db.session.add(welcome_tip)
            db.session.commit()
            
            # Log in the user
            login_user(new_user)
            
            # Redirect based on skip_onboarding preference
            if skip_onboarding:
                flash('Registration successful! Welcome to Smart Financial Analyzer', 'success')
                return redirect(url_for('main.dashboard'))
            else:
                flash('Registration successful! Let\'s personalize your experience', 'success')
                return redirect(url_for('auth.onboarding'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering user: {e}")
            
            # More specific error message
            if "duplicate key" in str(e).lower() and "username" in str(e).lower():
                flash('Username already exists. Please choose a different username.', 'danger')
            elif "duplicate key" in str(e).lower() and "email" in str(e).lower():
                flash('Email already registered. Please use a different email.', 'danger')
            else:
                flash('An error occurred during registration. Please try again.', 'danger')
                
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
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password', 'danger')
            return render_template('login.html')
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Log in the user
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
        dark_mode = 'dark_mode' in request.form
        daily_tip = 'daily_tip' in request.form
        learning_notifications = 'learning_notifications' in request.form
        
        # Validate input
        if not username or not email:
            flash('Username and email are required', 'danger')
            return redirect(url_for('auth.profile'))
        
        # Check if email is already taken by another user
        if email != current_user.email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Email already in use by another account', 'danger')
                return redirect(url_for('auth.profile'))
                
        # Check if username is already taken by another user
        if username != current_user.username:
            existing_username = User.query.filter_by(username=username).first()
            if existing_username and existing_username.id != current_user.id:
                flash('Username already taken by another account', 'danger')
                return redirect(url_for('auth.profile'))
        
        # Update preferences as a dictionary
        preferences = current_user.preferences or {}
        preferences['default_market'] = default_market
        preferences['dark_mode'] = dark_mode
        preferences['daily_tip'] = daily_tip
        preferences['learning_notifications'] = learning_notifications
        
        # Update user data
        current_user.username = username
        current_user.email = email
        current_user.preferences = preferences
        
        db.session.commit()
        
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
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('auth.profile'))
    
    # Update password
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    flash('Password updated successfully', 'success')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/update-preferences', methods=['POST'])
@login_required
def update_preferences():
    risk_profile = request.form.get('risk_profile', 'Moderate')
    investment_horizon = request.form.get('investment_horizon', 'Medium Term')
    
    # Get favorite sectors (will be a list if multiple selected, or a single value if one selected)
    favorite_sectors = request.form.getlist('favorite_sectors')
    
    # Notification settings
    email_alerts = 'email_alerts' in request.form
    price_alerts = 'price_alerts' in request.form
    news_alerts = 'news_alerts' in request.form
    
    # Update user preferences
    preferences = current_user.preferences or {}
    preferences['risk_profile'] = risk_profile
    preferences['investment_horizon'] = investment_horizon
    preferences['favorite_sectors'] = favorite_sectors
    
    # Update notification settings
    if 'notification_settings' not in preferences:
        preferences['notification_settings'] = {}
    
    preferences['notification_settings']['email_alerts'] = email_alerts
    preferences['notification_settings']['price_alerts'] = price_alerts
    preferences['notification_settings']['news_alerts'] = news_alerts
    
    # Save updated preferences
    current_user.preferences = preferences
    db.session.commit()
    
    flash('Investment preferences updated successfully', 'success')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/update-personal-profile', methods=['POST'])
@login_required
def update_personal_profile():
    # Get form data
    age_group = request.form.get('age_group', '')
    income_bracket = request.form.get('income_bracket', '')
    occupation = request.form.get('occupation', '')
    industry = request.form.get('industry', '')
    location = request.form.get('location', '')
    tax_bracket = request.form.get('tax_bracket', '')
    
    # Get numeric values - convert empty strings to None
    monthly_expenses = request.form.get('monthly_expenses', '')
    if monthly_expenses == '':
        monthly_expenses = None
    else:
        try:
            monthly_expenses = float(monthly_expenses)
        except ValueError:
            monthly_expenses = None
    
    loan_emi = request.form.get('loan_emi', '')
    if loan_emi == '':
        loan_emi = None
    else:
        try:
            loan_emi = float(loan_emi)
        except ValueError:
            loan_emi = None
    
    risk_tolerance_score = request.form.get('risk_tolerance_score', '5')
    try:
        risk_tolerance_score = int(risk_tolerance_score)
    except ValueError:
        risk_tolerance_score = 5
    
    investment_timeline = request.form.get('investment_timeline', '')
    if investment_timeline == '':
        investment_timeline = None
    else:
        try:
            investment_timeline = int(investment_timeline)
        except ValueError:
            investment_timeline = None
    
    # Get lists
    financial_goals = request.form.getlist('financial_goals')
    existing_investments = request.form.getlist('existing_investments')
    
    # Update user personal profile
    personal_profile = current_user.personal_profile or {}
    personal_profile.update({
        'age_group': age_group,
        'income_bracket': income_bracket,
        'occupation': occupation,
        'industry': industry,
        'location': location,
        'tax_bracket': tax_bracket,
        'monthly_expenses': monthly_expenses,
        'loan_emi': loan_emi,
        'risk_tolerance_score': risk_tolerance_score,
        'investment_timeline': investment_timeline,
        'financial_goals': financial_goals,
        'existing_investments': existing_investments
    })
    
    # Save updated personal profile
    current_user.personal_profile = personal_profile
    db.session.commit()
    
    flash('Personal information updated successfully', 'success')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/update-learning-preferences', methods=['POST'])
@login_required
def update_learning_preferences():
    # Get form data
    experience_level = request.form.get('experience_level', 'Beginner')
    preferred_learning_style = request.form.get('preferred_learning_style', 'Text')
    current_learning_path = request.form.get('current_learning_path', 'Basics')
    daily_quiz = 'daily_quiz' in request.form
    learning_topics = request.form.getlist('learning_topics')
    
    # Update personal profile for learning style and experience level
    personal_profile = current_user.personal_profile or {}
    personal_profile['experience_level'] = experience_level
    personal_profile['preferred_learning_style'] = preferred_learning_style
    current_user.personal_profile = personal_profile
    
    # Update learning progress
    learning_progress = current_user.learning_progress or {}
    learning_progress['current_learning_path'] = current_learning_path
    learning_progress['daily_quiz'] = daily_quiz
    learning_progress['learning_topics'] = learning_topics
    current_user.learning_progress = learning_progress
    
    db.session.commit()
    
    flash('Learning preferences updated successfully', 'success')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/onboarding')
@login_required
def onboarding():
    """Show the onboarding process for new users"""
    # Check if user has already completed personalization (to prevent going back to onboarding)
    personal_profile = current_user.personal_profile or {}
    if personal_profile.get('onboarding_completed'):
        flash('You have already completed the personalization process', 'info')
        return redirect(url_for('main.dashboard'))
    
    return render_template('onboarding.html')

@auth_bp.route('/save_onboarding', methods=['POST'])
@login_required
def save_onboarding():
    """Save the onboarding information"""
    # Get basic information
    age_group = request.form.get('age_group', '')
    location = request.form.get('location', '')
    occupation = request.form.get('occupation', '')
    industry = request.form.get('industry', '')
    
    # Get financial information
    income_bracket = request.form.get('income_bracket', '')
    tax_bracket = request.form.get('tax_bracket', '')
    
    # Parse numeric values
    monthly_expenses = request.form.get('monthly_expenses', '')
    if monthly_expenses and monthly_expenses.strip():
        try:
            monthly_expenses = float(monthly_expenses)
        except ValueError:
            monthly_expenses = None
    else:
        monthly_expenses = None
    
    loan_emi = request.form.get('loan_emi', '')
    if loan_emi and loan_emi.strip():
        try:
            loan_emi = float(loan_emi)
        except ValueError:
            loan_emi = None
    else:
        loan_emi = None
    
    # Get investment profile
    existing_investments = request.form.get('existing_investments', '')
    existing_investments = existing_investments.split(',') if existing_investments else []
    
    financial_goals = request.form.get('financial_goals', '')
    financial_goals = financial_goals.split(',') if financial_goals else []
    
    risk_tolerance_score = request.form.get('risk_tolerance_score', '5')
    try:
        risk_tolerance_score = int(risk_tolerance_score)
    except ValueError:
        risk_tolerance_score = 5
    
    # Get learning preferences
    experience_level = request.form.get('experience_level', 'Beginner')
    preferred_learning_style = request.form.get('preferred_learning_style', 'Text')
    
    # Get UI preferences
    daily_tip = 'daily_tip' in request.form
    learning_notifications = 'learning_notifications' in request.form
    dark_mode = 'dark_mode' in request.form
    
    # Update personal profile
    personal_profile = current_user.personal_profile or {}
    personal_profile.update({
        'age_group': age_group,
        'income_bracket': income_bracket,
        'occupation': occupation,
        'industry': industry,
        'location': location,
        'tax_bracket': tax_bracket,
        'monthly_expenses': monthly_expenses,
        'loan_emi': loan_emi,
        'risk_tolerance_score': risk_tolerance_score,
        'financial_goals': financial_goals,
        'existing_investments': existing_investments,
        'experience_level': experience_level,
        'preferred_learning_style': preferred_learning_style,
        'onboarding_completed': True
    })
    
    # Update preferences
    preferences = current_user.preferences or {}
    preferences.update({
        'risk_profile': 'Conservative' if risk_tolerance_score <= 3 else 'Moderate' if risk_tolerance_score <= 7 else 'Aggressive',
        'investment_horizon': 'Medium Term',  # Default to medium term since we removed the field
        'dark_mode': dark_mode,
        'daily_tip': daily_tip,
        'learning_notifications': learning_notifications
    })
    
    # Update learning progress
    learning_progress = current_user.learning_progress or {}
    learning_progress.update({
        'difficulty_level': experience_level,
        'current_learning_path': 'Basics' if experience_level == 'Beginner' else 'Intermediate' if experience_level == 'Intermediate' else 'Advanced'
    })
    
    # Save all updates
    current_user.personal_profile = personal_profile
    current_user.preferences = preferences
    current_user.learning_progress = learning_progress
    
    try:
        db.session.commit()
        flash('Your profile has been personalized! Welcome to Smart Financial Analyzer', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving onboarding data: {e}")
        flash('An error occurred while saving your preferences', 'danger')
    
    return redirect(url_for('main.dashboard'))
