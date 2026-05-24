from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.landing, name='landing'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Student
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('suggestions/', views.suggestions, name='suggestions'),

    # Chatbot
    path('chat/', views.chatbot, name='chatbot'),
    path('chat/new/', views.new_chat_session, name='new_chat'),
    path('chat/send/', views.send_message, name='send_message'),
    path('chat/session/<int:session_id>/', views.get_session_messages, name='get_session'),
    path('chat/delete/<int:session_id>/', views.delete_chat_session, name='delete_session'),

    # Interview
    path('interview/', views.interview_list, name='interview_list'),
    path('interview/start/', views.start_interview, name='start_interview'),
    path('interview/session/<int:interview_id>/', views.interview_session, name='interview_session'),
    path('interview/submit/', views.submit_answer, name='submit_answer'),
    path('interview/result/<int:interview_id>/', views.interview_result, name='interview_result'),

    # Reminders
    path('reminders/', views.reminders, name='reminders'),
    path('reminders/complete/<int:reminder_id>/', views.complete_reminder, name='complete_reminder'),
    path('reminders/delete/<int:reminder_id>/', views.delete_reminder, name='delete_reminder'),

    # Progress
    path('progress/', views.progress, name='progress'),
    path('progress/skill/', views.update_skill, name='update_skill'),

    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/students/', views.admin_students, name='admin_students'),
    path('admin-dashboard/students/<int:user_id>/', views.admin_student_detail, name='admin_student_detail'),
    path('admin-dashboard/analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin-dashboard/announcement/', views.create_announcement, name='create_announcement'),
]
