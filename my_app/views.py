from datetime import timedelta

from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import redirect, render

from . import models
from .decorators import login_required, post_only
from .models import Exam, PomodoroHistory, Session, Task, User
from .utils import format_duration


# =================================================================
# AUTHENTICATION

def index(request):
    if request.session.get('is_logged'):
        return redirect('/dashboard')
    return render(request, 'index.html')


def signup_page(request):
    return render(request, 'signup.html')


@post_only
def signup(request):
    errors = User.objects.validate_signup(request.POST)
    if errors:
        context = {
            'errors': errors,
            'username': request.POST.get('username', ''),
            'email': request.POST.get('email', ''),
        }
        return render(request, 'signup.html', context)

    user = models.create_user(request.POST)
    request.session['user_id'] = user.id
    request.session['is_logged'] = True
    return redirect('/dashboard')


def login_page(request):
    return render(request, 'login.html')


@post_only
def login(request):
    email = request.POST.get('email', '')
    errors = User.objects.validate_login(request.POST)

    if not errors:
        user = models.authenticate(email, request.POST.get('password', ''))
        if user:
            request.session['user_id'] = user.id
            request.session['is_logged'] = True
            return redirect('/dashboard')
        errors['password'] = 'Incorrect password.'

    return render(request, 'login.html', {'errors': errors, 'email': email})


def sign_out(request):
    request.session.flush()
    return redirect('/')


# =================================================================
# DASHBOARD

@login_required
def dashboard(request):
    user = models.get_user_by_id(request.session['user_id'])
    exams = models.get_all_exams_for_user(user)

    panic_level = max((exam.get_panic_level() for exam in exams), default=0)

    # Weekly study target = daily requirement x 7 (an exact split, not an
    # independent estimate - dividing it back by 7 always reproduces the
    # daily requirement exactly, so the two numbers can never disagree).
    daily_req = Exam.get_total_daily_required_minutes(user)
    daily_req_minutes = daily_req['hours'] * 60 + daily_req['minutes']
    weekly_target_minutes = daily_req_minutes * 7

    # "This week" = the same trailing 7-day PomodoroHistory window the chart
    # uses, NOT user.minutes_studied (a separate lifetime counter).
    weekly_study_minutes = models.get_weekly_study_minutes(user)

    context = {
        'user': user,
        'exams': exams,
        'total_exams': exams.count(),
        'all_minutes': user.minutes_studied,
        'hours': weekly_study_minutes // 60,
        'minutes': weekly_study_minutes % 60,
        'weekly_hours_display': format_duration(weekly_study_minutes),
        'sessions': user.sessions_completed,
        'today_required_hours': models.get_all_exams_required_hrs(user),
        'today_completed_hours': models.get_all_exams_completed_hrs(user),
        'today_required_hours_all_tasks': daily_req,
        'daily_percentage': Exam.calculate_daily_percentage(user),
        'panic_level': panic_level,
        'weekly_target_hours': weekly_target_minutes // 60,
        'weekly_target_mins': weekly_target_minutes % 60,
        'weekly_target_display': format_duration(weekly_target_minutes),
    }
    return render(request, 'dashboard.html', context)


@login_required
def daily_hours_api(request):
    """Total study hours per day for the last 7 days (for the dashboard chart).

    Uses the same trailing 7-day window as the "Hours Studied This Week"
    card (models.get_current_week_range) so the two can't drift apart.
    """
    user_id = request.session['user_id']
    week_start, today = models.get_current_week_range()

    rows = (
        PomodoroHistory.objects
        .filter(user_id=user_id, created_at__date__range=(week_start, today))
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total_minutes=Sum('minutes'))
    )
    minutes_by_day = {row['day']: row['total_minutes'] or 0 for row in rows}

    labels, data = [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%a'))
        data.append(round(minutes_by_day.get(day, 0) / 60, 1))

    return JsonResponse({'labels': labels, 'data': data})


# =================================================================
# EXAMS

@login_required
def exams_page(request):
    user = models.get_user_by_id(request.session['user_id'])
    context = {
        'userId': user.id,
        'exams': models.get_all_exams_for_user(user),
    }
    return render(request, 'exam.html', context)


@login_required
@post_only
def add_exam(request):
    errors = Exam.objects.validate_exam(request.POST)
    if errors:
        return JsonResponse({'success': False, 'errors': errors})
    models.create_exam(request.POST)
    return JsonResponse({'success': True})


@login_required
@post_only
def update_exam(request):
    errors = Exam.objects.validate_exam(request.POST)
    if errors:
        return JsonResponse({'success': False, 'errors': errors})
    models.update_exam(request.POST)
    return JsonResponse({'success': True})


@login_required
@post_only
def delete_exam(request):
    models.delete_exam(request.POST)
    return redirect('/exams_page')


@login_required
def get_exam_task(request, taskId):
    task = Task.objects.filter(id=taskId).values(
        'exam_id', 'exam_id__title', 'id', 'title', 'completed'
    )
    return JsonResponse(list(task), safe=False)


# =================================================================
# TASKS

@login_required
@post_only
def add_task(request):
    models.create_task(request.POST)
    return redirect('/exams_page')


@login_required
@post_only
def check_task(request):
    task = models.check_task(request.POST)
    return JsonResponse({
        'success': True,
        'data': task.exam_id.get_completed_tasks(),
    })


@login_required
@post_only
def delete_task(request):
    models.delete_task(request.POST)
    return redirect('/exams_page')


@login_required
def get_tasks(request, exam_id):
    tasks = Task.objects.filter(exam_id=exam_id, completed=False).values(
        'id', 'title', 'completed'
    )
    return JsonResponse(list(tasks), safe=False)


@login_required
@post_only
def log_task(request):
    models.check_task(request.POST)
    return redirect('/pomodoro_page')


# =================================================================
# SESSIONS

@login_required
def sessions_page(request):
    user = models.get_user_by_id(request.session['user_id'])
    context = {
        'userId': user.id,
        'sessions': models.get_all_sessions(),
    }
    return render(request, 'session.html', context)


@login_required
@post_only
def add_session(request):
    errors = Session.objects.validate_session(request.POST)
    if errors:
        return JsonResponse({'success': False, 'errors': errors})
    models.create_session(request.POST)
    return JsonResponse({'success': True})


@login_required
@post_only
def update_session(request):
    errors = Session.objects.validate_session(request.POST, session_id=request.POST.get('session_id'))
    if errors:
        return JsonResponse({'success': False, 'update_errors': errors})
    models.update_session(request.POST)
    return JsonResponse({'success': True})


@login_required
@post_only
def delete_session(request):
    models.delete_session(request.POST)
    return redirect('/sessions_page')


@login_required
@post_only
def attend_session(request):
    session = Session.objects.get(id=request.POST['session_id'])
    user = models.get_user_by_id(request.POST['user_id'])

    if session.attendees.filter(id=user.id).exists():
        return JsonResponse({
            'success': False,
            'message': 'You are already attending this session',
        })

    session.attendees.add(user)
    return JsonResponse({
        'success': True,
        'attendee_count': session.attendees.count(),
        'message': 'Successfully registered for session',
    })


# =================================================================
# POMODORO

@login_required
def pomodoro_page(request):
    user = models.get_user_by_id(request.session['user_id'])
    context = {
        'exams': models.get_all_exams_for_user(user),
        'minutes': user.minutes_studied,
        'sessions': user.sessions_completed,
    }
    return render(request, 'pomodoro.html', context)


@login_required
@post_only
def pomodoroForm(request):
    models.update_minutes(request.POST, request.session['user_id'])
    return redirect('/pomodoro_page')


# =================================================================
# ABOUT

def about(request):
    return render(request, 'about.html')
