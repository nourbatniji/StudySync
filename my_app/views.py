from django.shortcuts import render, redirect
from . import models 
from .models import User, Session, Exam, Task, PomodoroHistory
import bcrypt
from datetime import date, timedelta, datetime
from django.http import JsonResponse
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils import timezone



# Create your views here.
#=================================================================
# AUTHERNTICATION
def index(request):
    request.session['is_logged'] = False
    return render(request, 'index.html')

def signup_page(request):
    return render(request, 'signup.html')

def signup(request):
    if request.method == 'POST':
        errors = User.objects.validate_signup(request.POST)
        if errors:
            context = {
                'errors' : errors
            }
            request.session['is_logged'] = False
            return render(request, 'signup.html', context)
        else:
            user = models.create_user(request.POST)
            print('registerd')
            request.session['user_id'] = user.id
            request.session['is_logged'] = True
            return redirect('/dashboard')

def login_page(request):
    request.session['is_logged'] = False
    return render(request, 'login.html')

def login(request):
    if request.method == 'POST':
        errors = User.objects.validate_login(request.POST)
        user = models.get_user_by_email(request.POST['email'])
        if errors:
            context = {
                'errors' : errors
            }
            request.session['is_logged'] = False
            return render(request, 'login.html', context)
        else:
            if user:
                logged_user = user[0]
                if bcrypt.checkpw(request.POST['password'].encode(), logged_user.password.encode()):
                    request.session['user_id'] = logged_user.id
                    request.session['is_logged'] = True
                    print("logged")
                    return redirect('/dashboard')
                else:
                    request.session['is_logged'] = False
                    errors['incorrect_pw'] = "Incorrect Password"
                    context = {
                        "errors" : errors
                    }
                    return render(request, 'login.html', context)
                
def sign_out(request):
    request.session.flush()
    return render(request,'index.html')



#=================================================================
# DASHBOARD

def daily_hours_api(request):
    # 1) get current user id from session
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'not logged in'}, status=401)

    # 2) date range (last 7 days)
    today = timezone.localdate()
    week_start = today - timedelta(days=6)

    # 3) group PomodoroHistory by DATE(created_at) and sum minutes
    qs = (
        PomodoroHistory.objects
        .filter(
            user_id=user_id,                     # ✅ simpler + correct
            created_at__date__gte=week_start,
            created_at__date__lte=today,
        )
        .annotate(day=TruncDate('created_at'))  # group by day
        .values('day')
        .annotate(total_minutes=Sum('minutes'))
        .order_by('day')
    )

    # DEBUG – leave this for now to see what’s happening in the terminal
    print("DEBUG: Pomo rows for user", user_id)
    for row in qs:
        print(row)

    # 4) map {date: minutes}
    minutes_by_day = {row['day']: row['total_minutes'] or 0 for row in qs}

    labels = []
    data = []

    # 5) always return 7 days (even if 0)
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%a'))      # Fri, Sat...

        minutes = minutes_by_day.get(day, 0)
        data.append(round(minutes / 60, 1))    # minutes → hours

    return JsonResponse({'labels': labels, 'data': data})
def dashboard(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    user_id = request.session["user_id"]
    user = User.objects.get(id=user_id)

    # mins & hrs studied
    hours = user.minutes_studied // 60
    mins = user.minutes_studied % 60
    
    # Calculate overall panic level (highest panic level among all exams)
    exams = models.get_all_exams_for_user(user)
    panic_level = 0
    if exams:
        panic_level = max(exam.get_panic_level() for exam in exams)
    
    # Calculate weekly study target (daily requirement × 7)
    daily_req = Exam.get_total_daily_required_minutes(user)
    weekly_target_minutes = (daily_req['hours'] * 60 + daily_req['minutes']) * 7
    weekly_target_hours = weekly_target_minutes // 60
    weekly_target_mins = weekly_target_minutes % 60

    context = {
        'user' : models.get_user_by_id(request.session['user_id']),
        'exams' : exams,
        'total_exams' : Exam.objects.filter(user_id=user).count(),
        'all_minutes' : user.minutes_studied,
        'hours' : hours, 
        'minutes': mins,
        'sessions' : user.sessions_completed,
        'today_required_hours': models.get_all_exams_required_hrs(user),
        'today_required_hours_all_tasks' : daily_req,
        'daily_percentage' : Exam.calculate_daily_percentage(user),
        'panic_level': panic_level,
        'weekly_target_hours': weekly_target_hours,
        'weekly_target_mins': weekly_target_mins
    }
    return render(request, 'dashboard.html', context) 

# ---------------------------------------------------------------
# EXAMS
def exams_page(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    user = models.get_user_by_id(request.session['user_id'])
    user_id = user.id
    context = {
        'userId'  : user_id,
        'exams'  : models.get_all_exams_for_user(user),
    }
    return render(request, 'exam.html', context)

def add_exam(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    if request.method == 'POST':
        errors = Exam.objects.validate_exam(request.POST)
        print(errors)
        if errors:
            print(errors)
            return JsonResponse({
                'success' : False,
                'errors' : errors
            })
        else:
            models.create_exam(request.POST)
            return JsonResponse({
                'success' : True
            })
          
def delete_exam(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    if request.method == 'POST':
        models.delete_exam(request.POST)
        return redirect('/exams_page')
      
def update_exam(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    if request.method == 'POST':
        errors = Exam.objects.validate_exam(request.POST)
        if errors:
            return JsonResponse({
                'success' : False,
                'errors' : errors
            })
        else:
            models.update_exam(request.POST)
            return JsonResponse({
                'success' : True
            })
        
def get_exam_task(request, taskId):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    task = Task.objects.filter(id=taskId).values('exam_id','exam_id__title','id', 'title', 'completed')
    return JsonResponse(list(task), safe=False)
# ---------------------------------------------------------------
# TASKS

def add_task(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    if request.method == 'POST':
        models.create_task(request.POST)
        return redirect('/exams_page')

def check_task(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    if request.method == 'POST':
        task = models.check_task(request.POST)
        
        return JsonResponse({
            'success' : True,
            'data' : Exam.get_completed_tasks(task.exam_id)
        })
  

def delete_task(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    if request.method == 'POST':
        models.delete_task(request.POST)
        return redirect('/exams_page')
    
def get_tasks(request, exam_id):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    tasks = Task.objects.filter(exam_id=exam_id, completed=False).values('id', 'title', 'completed')
    return JsonResponse(list(tasks), safe=False)

#=================================================================
# SESSIONS

def sessions_page(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    user = models.get_user_by_id(request.session['user_id'])
    user_id = user.id
    context = {
        'userId'  : user_id,
        'sessions'  : models.get_all_sessions(),
    }
    return render(request, 'session.html', context)
 
def add_session(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    if request.method == 'POST':
        errors = Session.objects.validate_session(request.POST)
        if errors:
            print(errors)
            return JsonResponse({
                'success' : False,
                'errors' : errors
            })
        else:
            models.create_session(request.POST)
            return JsonResponse({
                'success' : True
            })
          
def update_session(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    if request.method == 'POST':
        update_errors = Session.objects.validate_session(request.POST)
        print(update_errors)
        if update_errors:
            print(update_errors)
            return JsonResponse({
                'success' : False,
                'update_errors' : update_errors
            })
        else:
            models.update_session(request.POST)
            return JsonResponse({
                'success' : True
            })
  
def delete_session(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    if request.method == 'POST':
        models.delete_session(request.POST)
        return redirect('/sessions_page')
      
def attend_session(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        user_id = request.POST.get('user_id')
        
        session = Session.objects.get(id=session_id)
        user = User.objects.get(id=user_id)
        
        # Check if user is already attending
        if session.attendees.filter(id=user_id).exists():
            return JsonResponse({
                'success': False,
                'message': 'You are already attending this session'
            })
        
        # Add user to attendees
        session.attendees.add(user)
        
        return JsonResponse({
            'success': True,
            'attendee_count': session.attendees.count(),
            'message': 'Successfully registered for session'
        })

    



#=================================================================
# POMODORO

def pomodoro_page(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    user_id = request.session["user_id"]
    user = User.objects.get(id=user_id)
    print("User minutes in DB:", user.minutes_studied)

    context = {
        'exams'  : models.get_all_exams_for_user(user),
        'minutes' : user.minutes_studied,
        'sessions' : user.sessions_completed,
    }
    return render(request, 'pomodoro.html', context)

def pomodoroForm(request):
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    if request.method == "POST":
        print("POST data in pomodoroForm:", request.POST)  # DEBUG
        user_id = request.session["user_id"]
        models.update_minutes(request.POST, user_id)
    return redirect('/pomodoro_page')

def log_task(request): 
    if not request.session.get('is_logged'):
        return render(request,'not_found.html')
    if request.method == "POST":
        models.log_task(request.POST)

    return redirect('/pomodoro_page')


# ==================================================================================================================
def about(request):    
    return render(request, 'about.html')
