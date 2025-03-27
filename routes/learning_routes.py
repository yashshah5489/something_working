from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import LearningResource, LearningPath, LearningBookmark, LearningProgress, DailyTip
from app import db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

learning_bp = Blueprint('learning', __name__, url_prefix='/learning')

@learning_bp.route('/')
@login_required
def home():
    """Learning homepage showing personalized resources and current progress"""
    # Get difficulty filter from query params or user's settings
    difficulty = request.args.get('difficulty', current_user.personal_profile.get('experience_level', 'Beginner'))
    
    # Get current learning path from user progress
    current_path_name = current_user.learning_progress.get('current_learning_path', 'Basics')
    current_path = LearningPath.query.filter_by(name=current_path_name).first()
    
    if not current_path:
        # Default path if user's path doesn't exist
        current_path = LearningPath.query.filter_by(difficulty_level=difficulty).first()
        if not current_path:
            # Create a default path if none exists
            current_path = create_default_learning_path(difficulty)
    
    # Get user's progress in current path
    path_progress = 0
    completed_resources = 0
    total_resources = len(current_path.resource_sequence) if current_path else 0
    
    progress_records = LearningProgress.query.filter_by(
        user_id=current_user.id,
        path_id=current_path.id if current_path else None
    ).all()
    
    if progress_records and total_resources > 0:
        completed_resources = sum(1 for p in progress_records if p.is_completed)
        path_progress = (completed_resources / total_resources) * 100 if total_resources > 0 else 0
    
    # Get next resource in learning path
    next_resource = None
    if current_path and current_path.resource_sequence:
        # Find the first resource not completed
        for resource_id in current_path.resource_sequence:
            progress = LearningProgress.query.filter_by(
                user_id=current_user.id, 
                resource_id=resource_id
            ).first()
            
            if not progress or not progress.is_completed:
                next_resource = LearningResource.query.get(resource_id)
                break
    
    # Get recommended resources based on user profile
    recommended_resources = get_recommended_resources(current_user, limit=3)
    
    # Get user's saved resources (bookmarks)
    saved_resources = LearningBookmark.query.filter_by(user_id=current_user.id).all()
    
    # Get daily tip if user has preference enabled
    daily_tip = None
    if current_user.preferences.get('daily_tip', True):
        # Check if user needs a new daily tip
        last_tip_time = current_user.last_daily_tip
        time_diff = datetime.utcnow() - last_tip_time if last_tip_time else timedelta(days=2)
        
        if time_diff.days >= 1:  # More than a day since last tip
            # Get personalized tip if available, otherwise get a general tip
            personalized_tip = DailyTip.query.filter_by(
                user_id=current_user.id,
                read=False,
                is_personalized=True
            ).order_by(DailyTip.created_at.desc()).first()
            
            if personalized_tip:
                daily_tip = personalized_tip
            else:
                # Get global tip based on user's difficulty level
                global_tip = DailyTip.query.filter_by(
                    user_id=None,  # Global tip
                    read=False,
                    tip_difficulty=difficulty
                ).order_by(DailyTip.created_at.desc()).first()
                
                if global_tip:
                    daily_tip = global_tip
                else:
                    # If no suitable tip found, create a default one
                    daily_tip = create_default_tip(current_user.id)
            
            # Update last tip time
            current_user.last_daily_tip = datetime.utcnow()
            db.session.commit()
    
    # Get all available learning paths for the modal
    all_paths = LearningPath.query.all()
    
    return render_template('learning.html', 
                          difficulty=difficulty,
                          current_path=current_path,
                          path_progress=path_progress,
                          completed_resources=completed_resources,
                          total_resources=total_resources,
                          next_resource=next_resource,
                          recommended_resources=recommended_resources,
                          saved_resources=saved_resources,
                          daily_tip=daily_tip,
                          all_paths=all_paths)

@learning_bp.route('/resource/<int:resource_id>')
@login_required
def resource(resource_id):
    """Display a specific learning resource"""
    resource = LearningResource.query.get_or_404(resource_id)
    
    # Check if resource is already bookmarked
    is_bookmarked = LearningBookmark.query.filter_by(
        user_id=current_user.id,
        resource_id=resource_id
    ).first() is not None
    
    # Get or create progress record
    progress = LearningProgress.query.filter_by(
        user_id=current_user.id,
        resource_id=resource_id
    ).first()
    
    if not progress:
        # Find the path this resource belongs to
        path = None
        for p in LearningPath.query.all():
            if resource_id in p.resource_sequence:
                path = p
                break
        
        progress = LearningProgress(
            user_id=current_user.id,
            resource_id=resource_id,
            path_id=path.id if path else None,
            last_accessed=datetime.utcnow()
        )
        db.session.add(progress)
        db.session.commit()
    else:
        # Update last accessed time
        progress.last_accessed = datetime.utcnow()
        db.session.commit()
    
    # Get related resources (same topic, same difficulty)
    related_resources = LearningResource.query.filter(
        LearningResource.topic == resource.topic,
        LearningResource.id != resource.id,
        LearningResource.difficulty_level == resource.difficulty_level
    ).limit(3).all()
    
    return render_template('learning_resource.html',
                          resource=resource,
                          is_bookmarked=is_bookmarked,
                          progress=progress,
                          related_resources=related_resources)

@learning_bp.route('/topic/<topic>')
@login_required
def topic(topic):
    """Display resources for a specific topic"""
    # Convert URL slug to readable format (e.g., "stock-market-basics" -> "Stock Market Basics")
    topic_name = topic.replace('-', ' ').title()
    
    # Get resources for this topic
    resources = LearningResource.query.filter_by(topic=topic_name).order_by(
        LearningResource.difficulty_level,
        LearningResource.duration_minutes
    ).all()
    
    # Group resources by difficulty level
    beginner_resources = [r for r in resources if r.difficulty_level == 'Beginner']
    intermediate_resources = [r for r in resources if r.difficulty_level == 'Intermediate']
    advanced_resources = [r for r in resources if r.difficulty_level == 'Advanced']
    
    return render_template('learning_topic.html',
                          topic=topic_name,
                          beginner_resources=beginner_resources,
                          intermediate_resources=intermediate_resources,
                          advanced_resources=advanced_resources)

@learning_bp.route('/bookmarks')
@login_required
def bookmarks():
    """Show user's bookmarked resources"""
    bookmarks = LearningBookmark.query.filter_by(user_id=current_user.id).all()
    return render_template('learning_bookmarks.html', bookmarks=bookmarks)

@learning_bp.route('/bookmark/<int:resource_id>', methods=['POST'])
@login_required
def add_bookmark(resource_id):
    """Add a resource to user's bookmarks"""
    # Check if resource exists
    resource = LearningResource.query.get_or_404(resource_id)
    
    # Check if already bookmarked
    existing_bookmark = LearningBookmark.query.filter_by(
        user_id=current_user.id,
        resource_id=resource_id
    ).first()
    
    if existing_bookmark:
        return jsonify({'success': False, 'message': 'Resource already bookmarked'})
    
    # Add bookmark
    notes = request.form.get('notes', '')
    bookmark = LearningBookmark(
        user_id=current_user.id,
        resource_id=resource_id,
        notes=notes
    )
    
    try:
        db.session.add(bookmark)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Resource bookmarked successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error bookmarking resource: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@learning_bp.route('/bookmarks/<int:bookmark_id>/remove', methods=['POST'])
@login_required
def remove_bookmark(bookmark_id):
    """Remove a bookmark"""
    bookmark = LearningBookmark.query.get_or_404(bookmark_id)
    
    # Ensure the bookmark belongs to current user
    if bookmark.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        db.session.delete(bookmark)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Bookmark removed successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing bookmark: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@learning_bp.route('/complete/<int:resource_id>', methods=['POST'])
@login_required
def mark_complete(resource_id):
    """Mark a learning resource as completed"""
    progress = LearningProgress.query.filter_by(
        user_id=current_user.id,
        resource_id=resource_id
    ).first()
    
    if not progress:
        return jsonify({'success': False, 'message': 'Progress record not found'})
    
    # Update quiz score if provided
    quiz_score = request.form.get('quiz_score')
    if quiz_score is not None:
        try:
            progress.quiz_score = float(quiz_score)
        except ValueError:
            pass
    
    # Update time spent if provided
    time_spent = request.form.get('time_spent')
    if time_spent is not None:
        try:
            progress.time_spent_minutes += int(time_spent)
        except ValueError:
            pass
    
    # Mark as completed
    progress.is_completed = True
    progress.completion_percentage = 100
    progress.completed_at = datetime.utcnow()
    
    # Update user's learning progress JSON
    learning_progress = current_user.learning_progress or {}
    completed_topics = learning_progress.get('completed_topics', [])
    
    # Add resource's topic to completed topics if not already there
    resource = LearningResource.query.get(resource_id)
    if resource and resource.topic not in completed_topics:
        completed_topics.append(resource.topic)
        learning_progress['completed_topics'] = completed_topics
        current_user.learning_progress = learning_progress
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Resource marked as completed'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marking resource as complete: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'})

@learning_bp.route('/update-progress/<int:resource_id>', methods=['POST'])
@login_required
def update_progress(resource_id):
    """Update progress on a learning resource (percentage completed)"""
    progress = LearningProgress.query.filter_by(
        user_id=current_user.id,
        resource_id=resource_id
    ).first()
    
    if not progress:
        return jsonify({'success': False, 'message': 'Progress record not found'})
    
    percentage = request.form.get('percentage')
    if percentage is not None:
        try:
            percentage = float(percentage)
            if 0 <= percentage <= 100:
                progress.completion_percentage = percentage
                
                # If 100%, mark as completed
                if percentage == 100:
                    progress.is_completed = True
                    progress.completed_at = datetime.utcnow()
                
                db.session.commit()
                return jsonify({'success': True, 'message': 'Progress updated'})
            else:
                return jsonify({'success': False, 'message': 'Percentage must be between 0 and 100'})
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid percentage'})
    
    return jsonify({'success': False, 'message': 'Percentage not provided'})

@learning_bp.route('/tips/<int:tip_id>/read', methods=['POST'])
@login_required
def mark_tip_read(tip_id):
    """Mark a daily tip as read"""
    tip = DailyTip.query.get_or_404(tip_id)
    
    # Ensure the tip belongs to current user or is global
    if tip.user_id is not None and tip.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    tip.read = True
    db.session.commit()
    return jsonify({'success': True, 'message': 'Tip marked as read'})

@learning_bp.route('/tips/<int:tip_id>/save', methods=['POST'])
@login_required
def save_tip(tip_id):
    """Save a daily tip for later"""
    tip = DailyTip.query.get_or_404(tip_id)
    
    # Ensure the tip belongs to current user or is global
    if tip.user_id is not None and tip.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    tip.saved = True
    db.session.commit()
    return jsonify({'success': True, 'message': 'Tip saved'})

@learning_bp.route('/change-path', methods=['POST'])
@login_required
def change_path():
    """Change user's current learning path"""
    path_id = request.form.get('learning_path_id')
    if not path_id:
        flash('No learning path selected', 'danger')
        return redirect(url_for('learning.home'))
    
    # Verify path exists
    path = LearningPath.query.get_or_404(path_id)
    
    # Update user's learning progress
    learning_progress = current_user.learning_progress or {}
    learning_progress['current_learning_path'] = path.name
    current_user.learning_progress = learning_progress
    
    db.session.commit()
    
    flash(f'Learning path changed to: {path.name}', 'success')
    return redirect(url_for('learning.home'))

# Helper functions
def get_recommended_resources(user, limit=3):
    """Get personalized resource recommendations based on user profile"""
    # Get user's difficulty level preference
    difficulty = user.personal_profile.get('experience_level', 'Beginner')
    
    # Get user's preferred learning style
    learning_style = user.personal_profile.get('preferred_learning_style', 'Text')
    
    # Get user's topics of interest
    topics_of_interest = user.learning_progress.get('learning_topics', [])
    
    # Get user's completed resources
    completed_resource_ids = []
    progress_records = LearningProgress.query.filter_by(
        user_id=user.id,
        is_completed=True
    ).all()
    
    for progress in progress_records:
        completed_resource_ids.append(progress.resource_id)
    
    # Query for recommendations
    query = LearningResource.query.filter(
        LearningResource.id.notin_(completed_resource_ids)
    )
    
    # Filter by difficulty
    query = query.filter_by(difficulty_level=difficulty)
    
    # Apply topic filter if topics of interest exist
    if topics_of_interest:
        query = query.filter(LearningResource.topic.in_(topics_of_interest))
    
    # Apply learning style preference if applicable
    if learning_style == 'Video':
        query = query.filter_by(resource_type='video')
    elif learning_style == 'Interactive':
        query = query.filter_by(resource_type='quiz')
    
    # Get resources ordered by relevance (most recent first)
    resources = query.order_by(LearningResource.created_at.desc()).limit(limit).all()
    
    # If not enough resources found, add some general ones
    if len(resources) < limit:
        additional_needed = limit - len(resources)
        additional_ids = [r.id for r in resources]  # Don't repeat resources already selected
        
        additional_resources = LearningResource.query.filter(
            LearningResource.id.notin_(completed_resource_ids + additional_ids)
        ).filter_by(
            difficulty_level=difficulty
        ).order_by(
            LearningResource.created_at.desc()
        ).limit(additional_needed).all()
        
        resources.extend(additional_resources)
    
    return resources

def create_default_learning_path(difficulty='Beginner'):
    """Create a default learning path if none exists"""
    path = LearningPath(
        name="Investment Basics" if difficulty == 'Beginner' else 
             "Advanced Investing" if difficulty == 'Advanced' else 
             "Intermediate Investing",
        description="A structured path to learn the fundamentals of investing in the Indian market.",
        target_audience="New Investors" if difficulty == 'Beginner' else 
                       "Experienced Investors" if difficulty == 'Advanced' else 
                       "Intermediate Investors",
        difficulty_level=difficulty,
        estimated_days=30 if difficulty == 'Beginner' else 45,
        topics_covered=["Stock Market Basics", "Mutual Funds", "Financial Planning"],
        resource_sequence=[]  # Will be populated as resources are added
    )
    
    db.session.add(path)
    db.session.commit()
    return path

def create_default_tip(user_id):
    """Create a default tip if none is available"""
    tip = DailyTip(
        user_id=user_id,
        tip_title="Start Your Investment Journey",
        tip_text="Begin with small investments to build your confidence and understanding of the market. Consider starting with mutual funds for diversification.",
        tip_category="investing",
        tip_difficulty="Beginner",
        is_personalized=True
    )
    
    db.session.add(tip)
    db.session.commit()
    return tip