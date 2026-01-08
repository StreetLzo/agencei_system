from flask_login import current_user
from flask import abort

def admin_required(func):
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)  # Forbidden
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper