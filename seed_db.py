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
        minutes_studied=500,
        sessions_completed=17
    )

    # Create additional mock users for group study sessions
    sarah = User.objects.create(
        username="Sarah Miller",
        email="sarah@test.com",
        password=hashed_pw,
        minutes_studied=320,
        sessions_completed=11
    )

    john = User.objects.create(
        username="John Doe",
        email="john@test.com",
        password=hashed_pw,
        minutes_studied=410,
        sessions_completed=14
    )

    print("Creating mock exams...")
    today = date.today()

    # Exam 1: Algorithms (Approaching in 5 days)
    algo_exam = Exam.objects.create(
        user_id=main_user,
        title="Algorithms & Data Structures",
        exam_date=today + timedelta(days=5)
    )

    # Exam 2: Database Design (Approaching in 9 days)
    db_exam = Exam.objects.create(
        user_id=main_user,
        title="Database Systems",
        exam_date=today + timedelta(days=9)
    )

    # Exam 3: Software Engineering (Approaching in 14 days)
    se_exam = Exam.objects.create(
        user_id=main_user,
        title="Software Architecture",
        exam_date=today + timedelta(days=14)
    )

    print("Creating mock tasks...")
    # Tasks for Algorithms
    Task.objects.create(user_id=main_user, exam_id=algo_exam, title="Big-O Notation & Complexity Analysis", priority=1, estimated_minutes=60, completed=True)
    Task.objects.create(user_id=main_user, exam_id=algo_exam, title="Sorting & Searching (QuickSort, MergeSort)", priority=2, estimated_minutes=90, completed=True)
    Task.objects.create(user_id=main_user, exam_id=algo_exam, title="Dynamic Programming & Recursion Practice", priority=3, estimated_minutes=150, completed=False)
    Task.objects.create(user_id=main_user, exam_id=algo_exam, title="Graph Traversals (BFS, DFS, Dijkstra)", priority=3, estimated_minutes=120, completed=False)
    Task.objects.create(user_id=main_user, exam_id=algo_exam, title="Hash Tables & Collision Resolution", priority=2, estimated_minutes=90, completed=False)

    # Tasks for Database Design
    Task.objects.create(user_id=main_user, exam_id=db_exam, title="Relational Database Schema Design", priority=1, estimated_minutes=60, completed=True)
    Task.objects.create(user_id=main_user, exam_id=db_exam, title="SQL Join Queries & Nested Selects", priority=2, estimated_minutes=120, completed=False)
    Task.objects.create(user_id=main_user, exam_id=db_exam, title="Database Normalization (1NF, 2NF, 3NF, BCNF)", priority=3, estimated_minutes=120, completed=False)
    Task.objects.create(user_id=main_user, exam_id=db_exam, title="Indexing & Query Performance Optimization", priority=2, estimated_minutes=90, completed=False)
    Task.objects.create(user_id=main_user, exam_id=db_exam, title="Transactions, ACID Properties & Lockings", priority=3, estimated_minutes=90, completed=False)

    # Tasks for Software Engineering
    Task.objects.create(user_id=main_user, exam_id=se_exam, title="Agile Software Development & Scrum Guide", priority=1, estimated_minutes=60, completed=True)
    Task.objects.create(user_id=main_user, exam_id=se_exam, title="SOLID Design Principles (OOP)", priority=2, estimated_minutes=120, completed=False)
    Task.objects.create(user_id=main_user, exam_id=se_exam, title="Architectural Patterns (MVC, Microservices)", priority=3, estimated_minutes=150, completed=False)
    Task.objects.create(user_id=main_user, exam_id=se_exam, title="Design Patterns (Factory, Singleton, Observer)", priority=2, estimated_minutes=120, completed=False)

    print("Creating pomodoro history for the past 7 days...")
    # Create study session history entries for the chart (grouped by date)
    # Today
    # NOTE: created_at uses auto_now_add, so it must be set with .update() after creation
    daily_minutes = [50, 75, 50, 100, 50, 125, 50]  # today, yesterday, ... 6 days ago
    for days_ago, minutes in enumerate(daily_minutes):
        entry = PomodoroHistory.objects.create(user=main_user, minutes=minutes)
        PomodoroHistory.objects.filter(id=entry.id).update(
            created_at=timezone.now() - timedelta(days=days_ago)
        )

    print("Creating mock study sessions...")
    # Session 1 (Tomorrow)
    sess1 = Session.objects.create(
        created_by=main_user,
        title="Algorithms Group Study",
        sess_date=today + timedelta(days=1),
        sess_time="14:00:00",
        duration=2,
        meet_link="https://meet.google.com/abc-defg-hij"
    )
    sess1.attendees.add(main_user, sarah, john)

    # Session 2 (In 3 days)
    sess2 = Session.objects.create(
        created_by=john,
        title="SQL & Joins Practice",
        sess_date=today + timedelta(days=3),
        sess_time="16:30:00",
        duration=3,
        meet_link="https://meet.google.com/xyz-qpur-wxy"
    )
    sess2.attendees.add(john, main_user, sarah)

    # Session 3 (In 4 days)
    sess3 = Session.objects.create(
        created_by=sarah,
        title="Software Architecture Patterns Discussion",
        sess_date=today + timedelta(days=4),
        sess_time="10:00:00",
        duration=2,
        meet_link="https://meet.google.com/mnp-tuvw-xyz"
    )
    sess3.attendees.add(sarah, main_user)

    print("Database successfully seeded!")
    print(f"Logged-in user email: nour@test.com")
    print(f"Logged-in user password: Password123!")

if __name__ == "__main__":
    seed_data()
