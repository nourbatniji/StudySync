from django.db import models
import re, bcrypt
from datetime import datetime, date

# Create your models here.
class UserManager(models.Manager):
    def validate_signup(self, postData):
        errors = {}
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        pass_regex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')

        if len(postData['username']) < 3 or len(postData['username']) > 25:
            errors['username_valid'] = 'Minimum 3 characters required'

        if not postData['username'].isalpha():
            errors['username_letter'] = 'Username must be letters only'

        if not email_regex.match(postData['email']):
            errors['email_valid'] = 'Invalid Email format'

        if is_exist(postData['email']) == True: 
            errors['not_unique']  = 'Email already exists'

        if not pass_regex.match(postData['password']) or len(postData['password']) > 128:
            errors['password_valid'] = 'Minimum 8 characters required'

        if postData['password'] != postData['confirm_pw']:
            errors['matching_pw'] = 'Passwords do not match!'

        return errors
    
    def validate_login(self, postData):
        login_errors = {}
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        pass_regex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')

        if not email_regex.match(postData['email']):
            login_errors['login_email_valid'] = 'Invalid Email format'

        if not is_exist(postData['email']):
            login_errors['login_email_noexist'] = 'Email does not exist'

        if not pass_regex.match(postData['password']) or len(postData['password']) > 128:
            login_errors['login_pass_valid'] = 'Minimum 8 characters required'

        return login_errors


class SessionManager(models.Manager):
    def validate_session(self, postData):
        sess_errors = {}
        # Title
        if len(postData['title']) < 2:
            sess_errors['title'] = 'Title must be at least 2 characters.' 

        # Date
        now = datetime.now().strftime("%Y-%m-%d")
        if postData['sess_date'] < now :
            sess_errors['date'] = 'Date must be in the future.' 
        
        # Url
        url_regex = re.compile(r'^(https?|ftp):\/\/[^\s\/$.?#].[^\s]*$')
        if not url_regex.match(postData['meet_link']):
            sess_errors['meet_link'] = 'Invalid URL' 
        if url_exist(postData['meet_link']):
            sess_errors['not_unique'] = 'This url is used'


        return sess_errors


class ExamManager(models.Manager):
    def validate_exam(self, postData):
        exam_errors = {}
        if len(postData['title']) < 2:
            exam_errors['title'] = 'Exam name must be at least 2 Characters'
        now = datetime.now().strftime('%Y-%m-%d')
        if postData['exam_date'] < now:
            exam_errors['exam_date'] = 'Exam cannot be in the past'
        return exam_errors
   

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
    def get_total_daily_required_minutes(user):
        total_minutes = 0
        exams = Exam.objects.filter(user_id=user)
        for exam in exams:
            data = exam.all_required_per_day()
            exam_minutes = data['hours'] * 60 + data['minutes']
            total_minutes += exam_minutes

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
    
    def calculate_daily_percentage(user):
    # remaining required time (not completed yet)
        remaining = get_all_exams_required_hrs(user)          # {'hours': h, 'minutes': m}

        # total required time (all tasks for this user)
        total = get_total_daily_required_minutes(user)    # {'hours': h, 'minutes': m}

        remaining_minutes = remaining['hours'] * 60 + remaining['minutes']
        total_minutes = total['hours'] * 60 + total['minutes']

        if total_minutes == 0:
            return 0

        done_minutes = total_minutes - remaining_minutes
        percentage = (done_minutes / total_minutes) * 100

        return round(percentage, 1)

    #number of days left till the exam
    def days_left(self):
        now = str(date.today())
        current_time = datetime.strptime(now, '%Y-%m-%d').date()
        days_left = self.exam_date - current_time
        return days_left.days
    
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
        username=postData['username'],
        email=postData['email'], 
        password=hashed_pw)

def is_exist(email): 
    return User.objects.filter(email=email).exists()

def get_user_by_email(email):
    return User.objects.filter(email=email)

def get_user_by_id(id):
    return User.objects.get(id=id)

def update_minutes(postData, user_id):
    minutes_str = postData.get("minutes", "").strip()

    if not minutes_str:
        return

    try:
        minutes = int(minutes_str)
    except ValueError:
        return
    
    user = User.objects.get(id=user_id)
    user.minutes_studied += minutes
    user.sessions_completed += 1
    user.save()

    PomodoroHistory.objects.create(
    user=user,
    minutes=minutes

    )
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

def get_total_daily_required_minutes(user):
    total_minutes = 0
    exams = Exam.objects.filter(user_id=user)
    for exam in exams:
        data = exam.all_required_per_day()
        exam_minutes = data['hours'] * 60 + data['minutes']
        total_minutes += exam_minutes

    return {
        'hours': total_minutes // 60,
        'minutes': total_minutes % 60
    } 

#get all required hours and exclude the completed  
def get_all_exams_required_hrs(user):
    T_hours = 0
    T_minutes = 0

    for exam in get_all_exams_for_user(user):
        data = exam.total_hours_per_day()
        T_hours += data['hours']
        T_minutes += data['minutes']

    return {
        'hours': T_hours,
        'minutes': T_minutes
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

def get_tasks(exam_id):
    tasks = Task.objects.filter(exam_id=exam_id)
    return tasks

def log_task(postData):
    task = Task.objects.get(id=postData['task_id'])
    task.completed = not task.completed
    task.save()

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

def url_exist(meet_link):
    return Session.objects.filter(meet_link=meet_link).exists()

def update_session(postData):
    session = Session.objects.get(id=postData['session_id'])
    session.title = postData['title']
    session.sess_date = postData['sess_date']
    session.sess_time = postData['sess_time']
    session.duration= postData['duration']
    session.meet_link = postData['meet_link']
    session.save()

def attend_session(postData):
    session = Session.objects.get(id=postData['session_id'])
    user = User.objects.get(id=postData['user_id'])
    session.attendees.add(user)
    return session.attendees.count()