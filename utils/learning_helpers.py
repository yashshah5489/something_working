from flask import current_app
from models import LearningPath, LearningResource, LearningProgress, LearningBookmark
from collections import defaultdict

def get_learning_path(path_id):
    """Helper to get a learning path by ID"""
    return LearningPath.query.get(path_id)

def get_resource(resource_id):
    """Helper to get a learning resource by ID"""
    return LearningResource.query.get(resource_id)

def get_path_progress(user_id, path_id):
    """Helper to get a user's progress percentage on a learning path"""
    path = LearningPath.query.get(path_id)
    if not path or not path.resource_sequence:
        return 0
    
    # Get all user's progress records for this path
    progress_records = LearningProgress.query.filter_by(
        user_id=user_id,
        path_id=path_id,
        is_completed=True
    ).all()
    
    # Calculate completion percentage
    completed_resource_ids = [p.resource_id for p in progress_records]
    total_resources = len(path.resource_sequence)
    completed_path_resources = sum(1 for r_id in path.resource_sequence if r_id in completed_resource_ids)
    
    return (completed_path_resources / total_resources) * 100 if total_resources > 0 else 0

def get_completed_resources_count(user_id, path_id):
    """Helper to get the count of completed resources on a learning path"""
    path = LearningPath.query.get(path_id)
    if not path or not path.resource_sequence:
        return 0
    
    # Get all user's progress records for this path
    progress_records = LearningProgress.query.filter_by(
        user_id=user_id,
        path_id=path_id,
        is_completed=True
    ).all()
    
    # Calculate completed resources that are part of this path
    completed_resource_ids = [p.resource_id for p in progress_records]
    completed_path_resources = sum(1 for r_id in path.resource_sequence if r_id in completed_resource_ids)
    
    return completed_path_resources

def is_resource_completed(user_id, resource_id):
    """Helper to check if a resource is completed by the user"""
    progress = LearningProgress.query.filter_by(
        user_id=user_id,
        resource_id=resource_id,
        is_completed=True
    ).first()
    
    return progress is not None

def get_resource_progress(user_id, resource_id):
    """Helper to get a user's progress on a specific resource"""
    return LearningProgress.query.filter_by(
        user_id=user_id,
        resource_id=resource_id
    ).first()

def get_completed_bookmark_count(user_id, bookmarks):
    """Helper to get the count of completed bookmarked resources"""
    completed_count = 0
    for bookmark in bookmarks:
        if is_resource_completed(user_id, bookmark.resource_id):
            completed_count += 1
    return completed_count

def get_not_started_bookmark_count(user_id, bookmarks):
    """Helper to get the count of bookmarked resources not started yet"""
    not_started_count = 0
    for bookmark in bookmarks:
        progress = get_resource_progress(user_id, bookmark.resource_id)
        if progress is None or progress.completion_percentage == 0:
            not_started_count += 1
    return not_started_count

def get_bookmarks_with_notes_count(bookmarks):
    """Helper to get the count of bookmarks with notes"""
    return sum(1 for bookmark in bookmarks if bookmark.notes)

def get_bookmark_topics(bookmarks):
    """Helper to get topics of bookmarked resources with counts"""
    topics = defaultdict(int)
    for bookmark in bookmarks:
        if bookmark.resource and bookmark.resource.topic:
            topics[bookmark.resource.topic] += 1
    
    return dict(topics)

# Register these functions with the app context
def register_learning_helpers(app):
    """Register all learning helper functions with the app context"""
    @app.context_processor
    def inject_learning_helpers():
        return {
            'get_learning_path': get_learning_path,
            'get_resource': get_resource,
            'get_path_progress': get_path_progress,
            'get_completed_resources_count': get_completed_resources_count,
            'is_resource_completed': is_resource_completed,
            'get_resource_progress': get_resource_progress,
            'get_completed_bookmark_count': get_completed_bookmark_count,
            'get_not_started_bookmark_count': get_not_started_bookmark_count,
            'get_bookmarks_with_notes_count': get_bookmarks_with_notes_count,
            'get_bookmark_topics': get_bookmark_topics
        }