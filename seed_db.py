import os
import django
from datetime import date, timedelta
import bcrypt

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Study_Sync2.settings')
django.setup()

from django.utils import timezone

from my_app.models import User, Exam, Task, Session, PomodoroHistory

def seed_data():
    print("Deleting old mock data...")
    # Clean database
    PomodoroHistory.objects.all().delete()
    Task.objects.all().delete()
    Exam.objects.all().delete()
    Session.objects.all().delete()
    User.objects.all().delete()

    print("Creating mock users...")
    # Create main user
    password = "Password123!"
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    main_user = User.objects.create(
        username="Nour",
        email="nour@test.com",
        password=hashed_pw,
        minutes_studied=640,
        sessions_completed=21
    )

    # Create additional mock users for group study sessions
    sarah = User.objects.create(
        username="Sarah Miller",
        email="sarah@test.com",
        password=hashed_pw,
        minutes_studied=380,
        sessions_completed=13
    )

    john = User.objects.create(
        username="John Doe",
        email="john@test.com",
        password=hashed_pw,
        minutes_studied=455,
        sessions_completed=16
    )

    layla = User.objects.create(
        username="Layla Hassan",
        email="layla@test.com",
        password=hashed_pw,
        minutes_studied=290,
        sessions_completed=9
    )

    print("Creating mock exams...")
    today = date.today()

    # Exam 1: Operating Systems (in 3 days, ~33% done -> ORANGE alert, panic level 2)
    os_exam = Exam.objects.create(
        user_id=main_user,
        title="Operating Systems",
        exam_date=today + timedelta(days=3)
    )

    # Exam 2: Computer Networks (in 8 days, 40% done -> warning level 1)
    net_exam = Exam.objects.create(
        user_id=main_user,
        title="Computer Networks",
        exam_date=today + timedelta(days=8)
    )

    # Exam 3: Machine Learning (in 16 days, 75% done -> on track, level 0)
    ml_exam = Exam.objects.create(
        user_id=main_user,
        title="Machine Learning Fundamentals",
        exam_date=today + timedelta(days=16)
    )

    print("Creating mock tasks...")
    # Tasks for Operating Systems (6 tasks, 2 completed -> ~33% progress)
    Task.objects.create(user_id=main_user, exam_id=os_exam, title="Processes vs Threads & Context Switching", priority=1, estimated_minutes=60, completed=True)
    Task.objects.create(user_id=main_user, exam_id=os_exam, title="CPU Scheduling (FCFS, SJF, Round Robin)", priority=2, estimated_minutes=90, completed=True)
    Task.objects.create(user_id=main_user, exam_id=os_exam, title="Deadlocks: Detection, Prevention, Avoidance", priority=3, estimated_minutes=120, completed=False)
    Task.objects.create(user_id=main_user, exam_id=os_exam, title="Memory Management & Paging", priority=3, estimated_minutes=150, completed=False)
    Task.objects.create(user_id=main_user, exam_id=os_exam, title="Virtual Memory & Page Replacement", priority=2, estimated_minutes=90, completed=False)
    Task.objects.create(user_id=main_user, exam_id=os_exam, title="File Systems & I/O Management", priority=2, estimated_minutes=90, completed=False)

    # Tasks for Computer Networks (5 tasks, 2 completed -> 40% progress)
    Task.objects.create(user_id=main_user, exam_id=net_exam, title="OSI & TCP/IP Layer Models", priority=1, estimated_minutes=60, completed=True)
    Task.objects.create(user_id=main_user, exam_id=net_exam, title="IP Addressing & Subnetting Practice", priority=2, estimated_minutes=120, completed=True)
    Task.objects.create(user_id=main_user, exam_id=net_exam, title="TCP vs UDP, Handshakes & Flow Control", priority=3, estimated_minutes=90, completed=False)
    Task.objects.create(user_id=main_user, exam_id=net_exam, title="Routing Algorithms (OSPF, BGP, RIP)", priority=3, estimated_minutes=120, completed=False)
    Task.objects.create(user_id=main_user, exam_id=net_exam, title="DNS, HTTP/HTTPS & Application Layer", priority=2, estimated_minutes=90, completed=False)

    # Tasks for Machine Learning (4 tasks, 3 completed -> 75% progress)
    Task.objects.create(user_id=main_user, exam_id=ml_exam, title="Linear & Logistic Regression", priority=1, estimated_minutes=90, completed=True)
    Task.objects.create(user_id=main_user, exam_id=ml_exam, title="Decision Trees & Random Forests", priority=2, estimated_minutes=90, completed=True)
    Task.objects.create(user_id=main_user, exam_id=ml_exam, title="Overfitting, Regularization & Cross-Validation", priority=2, estimated_minutes=60, completed=True)
    Task.objects.create(user_id=main_user, exam_id=ml_exam, title="Neural Networks & Backpropagation Basics", priority=3, estimated_minutes=150, completed=False)

    print("Creating pomodoro history for the past 7 days...")
    # Create study session history entries for the chart (grouped by date)
    # NOTE: created_at uses auto_now_add, so it must be set with .update() after creation
    daily_minutes = [80, 45, 110, 60, 95, 30, 120]  # today, yesterday, ... 6 days ago
    for days_ago, minutes in enumerate(daily_minutes):
        entry = PomodoroHistory.objects.create(user=main_user, minutes=minutes)
        PomodoroHistory.objects.filter(id=entry.id).update(
            created_at=timezone.now() - timedelta(days=days_ago)
        )

    print("Creating mock study sessions...")
    # Session 1 (Tomorrow)
    sess1 = Session.objects.create(
        created_by=main_user,
        title="OS Scheduling & Deadlocks Review",
        sess_date=today + timedelta(days=1),
        sess_time="15:00:00",
        duration=2,
        meet_link="https://meet.google.com/osx-revw-abc"
    )
    sess1.attendees.add(main_user, sarah, layla)

    # Session 2 (In 2 days)
    sess2 = Session.objects.create(
        created_by=john,
        title="Subnetting & Routing Practice",
        sess_date=today + timedelta(days=2),
        sess_time="17:30:00",
        duration=3,
        meet_link="https://meet.google.com/net-prac-xyz"
    )
    sess2.attendees.add(john, main_user, sarah)

    # Session 3 (In 5 days)
    sess3 = Session.objects.create(
        created_by=layla,
        title="ML Study Jam: Neural Networks",
        sess_date=today + timedelta(days=5),
        sess_time="11:00:00",
        duration=2,
        meet_link="https://meet.google.com/mlj-stud-nnw"
    )
    sess3.attendees.add(layla, main_user, john)

    print("Database successfully seeded!")
    print(f"Logged-in user email: nour@test.com")
    print(f"Logged-in user password: Password123!")

if __name__ == "__main__":
    seed_data()
