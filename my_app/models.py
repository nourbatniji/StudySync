import re
from datetime import date, datetime

import bcrypt
from django.db import models

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,128}$')
URL_REGEX = re.compile(r'^(https?|ftp)://[^\s/$.?#].[^\s]*$')


class UserManager(models.Manager):
    def validate_signup(self, postData):
        errors = {}
        username = postData.get('username', '').strip()
        email = postData.get('email', '').strip()
        password = postData.get('password', '')

        if not 3 <= len(username) <= 25:
            errors['username'] = 'Name must be between 3 and 25 characters.'
        elif not username.replace(' ', '').isalpha():
            errors['username'] = 'Name must contain letters only.'

        if not EMAIL_REGEX.match(email):
            errors['email'] = 'Invalid email format.'
        elif self.filter(email=email).exists():
            errors['email'] = 'This email is already registered.'

        if not PASSWORD_REGEX.match(password):
            errors['password'] = ('Password must be 8-128 characters and include an uppercase letter, '
                                  'a lowercase letter, a number, and a special character (@$!%*?&).')

        if password != postData.get('confirm_pw', ''):
            errors['confirm_pw'] = 'Passwords do not match.'

        return errors

    def validate_login(self, postData):
        errors = {}
        email = postData.get('email', '').strip()

        if not EMAIL_REGEX.match(email):
            errors['email'] = 'Invalid email format.'
        elif not self.filter(email=email).exists():
            errors['email'] = 'No account found with this email.'

        if not postData.get('password', ''):
            errors['password'] = 'Password is required.'

        return errors


class SessionManager(models.Manager):
    def validate_session(self, postData, session_id=None):
        errors = {}

        if len(postData.get('title', '')) < 2:
            errors['title'] = 'Title must be at least 2 characters.'

        today = date.today().strftime('%Y-%m-%d')
        if postData.get('sess_date', '') < today:
            errors['date'] = 'Date must be in the future.'

        meet_link = postData.get('meet_link', '')
        if not URL_REGEX.match(meet_link):
            errors['meet_link'] = 'Invalid URL.'
        else:
            duplicates = self.filter(meet_link=meet_link)
            if session_id:
                duplicates = duplicates.exclude(id=session_id)
            if duplicates.exists():
                errors['not_unique'] = 'This URL is already used by another session.'

        return errors


class ExamManager(models.Manager):
    def validate_exam(self, postData):
        errors = {}
        if len(postData.get('title', '')) < 2:
            errors['title'] = 'Exam name must be at least 2 characters.'
        today = date.today().strftime('%Y-%m-%d')
        if postData.get('exam_date', '') < today:
            errors['exam_date'] = 'Exam cannot be in the past.'
        return errors


class User(models.Model):
    username = models.CharField(max_length=45)
    email = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    minutes_studied = models.IntegerField(default=0)
    sessions_completed= models.IntegerField(default=0)
    objects = UserManager()
    #exams
    #user_tasks
    #user_sessions


class Exam(models.Model):
    user_id = models.ForeignKey(User, related_name='exams', on_delete=models.CASCADE)
    title = models.CharField(max_length=45)
    exam_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    #exam_tasks
    objects = ExamManager()
    def task_count(self):
        return self.exam_tasks.count()
    
    #daily hours required per day // completed tasks are excluded
    def total_hours_per_day(self):
        counter = 0
        for task in self.exam_tasks.all():
            if (task.completed == False):
                counter += task.estimated_minutes
        
        days = self.days_left()
        if days <= 0:
            return {'hours': 0, 'minutes': 0}
        
        total_per_day = counter / days

        return {
            'hours' : int(total_per_day // 60),
            'minutes' : int(total_per_day % 60)
        }
    
     #daily hours required per day // all in, nothing excluded // returns required per exam
    def all_required_per_day(self):
        counter = 0
        for task in self.exam_tasks.all():
            counter += task.estimated_minutes

        days = self.days_left()
        if days <= 0:
            return {'hours': 0, 'minutes': 0}
        
        total_per_day = counter / days

        return {
            'hours': int(total_per_day // 60),
            'minutes': int(total_per_day % 60)
        }
    @staticmethod
    def get_total_daily_required_minutes(user):
        """Total daily required time across all of a user's exams (all tasks included)."""
        total_minutes = 0
        for exam in Exam.objects.filter(user_id=user):
            data = exam.all_required_per_day()
            total_minutes += data['hours'] * 60 + data['minutes']

        return {
            'hours': total_minutes // 60,
            'minutes': total_minutes % 60
        }


    def done_task_count(self):
        return self.exam_tasks.filter(completed=True).count()

   
    #number of completed tasks
    def get_completed_tasks(self):
        counter = 0
        for task in self.exam_tasks.all():
            if task.completed == True:
                counter += 1
        return counter
    
    # % done tasks of all tasks
    def percentage(self):
        total_tasks = self.task_count()
        if total_tasks == 0:
            return 0
        return (self.get_completed_tasks()/total_tasks)*100
    
    @staticmethod
    def calculate_daily_percentage(user):
        """% of today's required study time already done (completed tasks vs all tasks)."""
        remaining = get_all_exams_required_hrs(user)                 # {'hours': h, 'minutes': m}
        total = Exam.get_total_daily_required_minutes(user)          # {'hours': h, 'minutes': m}

        remaining_minutes = remaining['hours'] * 60 + remaining['minutes']
        total_minutes = total['hours'] * 60 + total['minutes']

        if total_minutes == 0:
            return 0

        done_minutes = total_minutes - remaining_minutes
        percentage = (done_minutes / total_minutes) * 100

        return round(percentage, 1)

    #number of days left till the exam
    def days_left(self):
        return (self.exam_date - date.today()).days
    
    def urgency_color(self):
        days = self.days_left()
        progress = self.percentage()

        # Critical: Less than 3 days OR very low progress
        if days <= 2 or (days <= 5 and progress < 20):
            return "#dc3545"     # red
        # Warning: Less than 7 days OR low progress  
        if days <= 7 or (days <= 14 and progress < 50):
            return "#ffc107"     # yellow
        # Good: More than 7 days and decent progress
        return "#28a745"         # green
    
    def get_panic_level(self):
        """Returns panic level 0-3 based on days left and progress"""
        days = self.days_left()
        progress = self.percentage()
        
        # Level 3: CRITICAL - Exam very soon with low progress
        if days <= 1 or (days <= 3 and progress < 30):
            return 3
        # Level 2: HIGH ALERT - Exam approaching with insufficient progress
        if days <= 3 or (days <= 7 and progress < 40):
            return 2
        # Level 1: WARNING - Some concern
        if days <= 7 or (days <= 14 and progress < 60):
            return 1
        # Level 0: ON TRACK
        return 0 


class Task(models.Model):
    user_id = models.ForeignKey(User, related_name='user_tasks', on_delete=models.CASCADE)
    exam_id = models.ForeignKey(Exam, related_name='exam_tasks', on_delete=models.CASCADE)
    title = models.CharField(max_length=45)
    priority = models.IntegerField(default=1)
    estimated_minutes = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # task_sessions


class Session(models.Model):
    created_by = models.ForeignKey(User, related_name='user_created_sessions', on_delete=models.CASCADE)
    attendees = models.ManyToManyField(User, related_name='user_attendings_sessions')
    title = models.CharField(max_length=45)
    sess_date = models.DateField()
    sess_time = models.TimeField()
    duration = models.IntegerField()
    meet_link = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = SessionManager()


class PomodoroHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pomodoros')
    minutes = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

#=================================================================
# USER
def create_user(postData):
    hashed_pw = bcrypt.hashpw(postData['password'].encode(), bcrypt.gensalt()).decode()
    return User.objects.create(
        username=postData['username'].strip(),
        email=postData['email'].strip(),
        password=hashed_pw)

def authenticate(email, password):
    """Return the user if email + password are correct, otherwise None."""
    user = User.objects.filter(email=email.strip()).first()
    if user and bcrypt.checkpw(password.encode(), user.password.encode()):
        return user
    return None

def get_user_by_id(id):
    return User.objects.get(id=id)

def update_minutes(postData, user_id):
    try:
        minutes = int(postData.get('minutes', '').strip())
    except ValueError:
        return None

    user = User.objects.get(id=user_id)
    user.minutes_studied += minutes
    user.sessions_completed += 1
    user.save()

    PomodoroHistory.objects.create(user=user, minutes=minutes)
    return user.minutes_studied


#=================================================================
# EXAM
def create_exam(postData):
    user = User.objects.get(id=postData['user_id'])
    return Exam.objects.create(
        user_id = user,
        title = postData['title'],
        exam_date = postData['exam_date']
    )

def get_all_exams_for_user(user):
    return Exam.objects.filter(user_id=user).order_by('exam_date')

def delete_exam(postData):
    Exam.objects.filter(id=postData['exam_id']).delete()

def update_exam(postData):
    exam = Exam.objects.get(id=postData['exam_id'])
    exam.title = postData['title']
    exam.exam_date = postData['exam_date']
    exam.save()

#get all required hours and exclude the completed
def get_all_exams_required_hrs(user):
    total_minutes = 0

    for exam in get_all_exams_for_user(user):
        data = exam.total_hours_per_day()
        total_minutes += data['hours'] * 60 + data['minutes']

    return {
        'hours': total_minutes // 60,
        'minutes': total_minutes % 60
    }

#------------------------------------------------------------------
# TASK
def create_task(postData):#done
    user = User.objects.get(id=postData['user_id'])
    exam = Exam.objects.get(id=postData['exam_id'])
    hours = int(postData['hours'])
    minutes = int(postData['minutes'])
    estimated_minutes = hours * 60 + minutes

    return Task.objects.create(
        user_id = user,
        exam_id = exam,
        title = postData['title'],
        priority = postData['priority'],
        estimated_minutes = estimated_minutes,
    )

def check_task(postData):
    task = Task.objects.get(id = postData['task_id'])
    task.completed = not task.completed
    task.save()
    return task

def delete_task(postData):
    task = Task.objects.get(id = postData['task_id'])
    task.delete()

#------------------------------------------------------------------
# SESSION
def create_session(postData):
    created_by = User.objects.get(id=postData['user_id'])
    session = Session.objects.create(
        created_by = created_by,
        title = postData['title'],
        sess_date = postData['sess_date'],
        sess_time = postData['sess_time'],
        duration= postData['duration'],
        meet_link = postData['meet_link'],
    )
    session.attendees.add(created_by)
    return session

def delete_session(postData):
    session = Session.objects.get(id=postData['session_id'])
    session.delete()

def get_all_sessions():
    return Session.objects.all()

def update_session(postData):
    session = Session.objects.get(id=postData['session_id'])
    session.title = postData['title']
    session.sess_date = postData['sess_date']
    session.sess_time = postData['sess_time']
    session.duration= postData['duration']
    session.meet_link = postData['meet_link']
    session.save()