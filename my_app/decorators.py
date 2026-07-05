from functools import wraps

from django.shortcuts import render


def login_required(view_func):
    """Render 404 page if the user is not logged in."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_logged'):
            return render(request, 'not_found.html', status=404)
        return view_func(request, *args, **kwargs)
    return wrapper


def post_only(view_func):
    """Redirect to home if the request is not a POST."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method != 'POST':
            return render(request, 'not_found.html', status=404)
        return view_func(request, *args, **kwargs)
    return wrapper
