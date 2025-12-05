from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    # AUTHINTICATION
    path('signup_page', views.signup_page),
    path('signup', views.signup),
    path('login_page', views.login_page),
    path('login', views.login),
    path('signout', views.sign_out),


    path('dashboard', views.dashboard),


    path('exams_page', views.exams_page),
    path('add_exam/', views.add_exam),
    path('delete_exam', views.delete_exam),
    path('update_exam/', views.update_exam),
    path('get_exam_task/<int:taskId>/', views.get_exam_task),




    path('add_task', views.add_task),
    path('check_task/', views.check_task),
    path('delete_task', views.delete_task),
    path('get_tasks/<int:exam_id>/', views.get_tasks),
    path('log_task', views.log_task),


    path('sessions_page', views.sessions_page),
    path('add_session/', views.add_session),
    path('update_session/', views.update_session),
    path('delete_session', views.delete_session),
    path('attend_session', views.attend_session),


    path('pomodoro_page', views.pomodoro_page),
    path('pomodoroForm', views.pomodoroForm),
    path('api/daily-hours/', views.daily_hours_api, name='daily_hours_api'),



    path('about', views.about),



]