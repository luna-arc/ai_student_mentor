import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Sum, Count
from .models import (StudentProfile, ChatSession, ChatMessage, MockInterview,
                     InterviewQuestion, Reminder, ProgressRecord, SkillAssessment, Announcement)
from .ai_services import (get_academic_answer, generate_interview_question,
                           evaluate_interview_answer, generate_personalized_suggestions, chat_with_mentor)


# ─── Auth Views ───────────────────────────────────────────────────────────────

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('admin_dashboard' if user.is_staff else 'dashboard')
        messages.error(request, 'Invalid credentials. Please try again.')
    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        target_role = request.POST.get('target_role', '')
        skill_level = request.POST.get('skill_level', 'beginner')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'register.html')

        user = User.objects.create_user(username=username, email=email, password=password,
                                         first_name=first_name, last_name=last_name)
        StudentProfile.objects.create(user=user, target_role=target_role, skill_level=skill_level)
        login(request, user)
        messages.success(request, 'Welcome aboard! Your AI mentor is ready.')
        return redirect('dashboard')
    return render(request, 'register.html')


def logout_view(request):
    logout(request)
    return redirect('landing')


# ─── Student Dashboard ────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    
    # Update last active & streak
    today = timezone.now().date()
    if profile.last_active != today:
        if profile.last_active and (today - profile.last_active).days == 1:
            profile.streak_days += 1
        elif not profile.last_active or (today - profile.last_active).days > 1:
            profile.streak_days = 1
        profile.last_active = today
        profile.save()

    recent_progress = ProgressRecord.objects.filter(user=request.user)[:5]
    upcoming_reminders = Reminder.objects.filter(user=request.user, is_completed=False,
                                                  due_datetime__gte=timezone.now())[:3]
    recent_interviews = MockInterview.objects.filter(user=request.user)[:3]
    announcements = Announcement.objects.filter(is_active=True)[:3]
    
    # Stats
    total_interviews = MockInterview.objects.filter(user=request.user, status='completed').count()
    avg_score = MockInterview.objects.filter(user=request.user, status='completed'
                                             ).aggregate(Avg('overall_score'))['overall_score__avg'] or 0
    total_chats = ChatSession.objects.filter(user=request.user).count()
    skills = SkillAssessment.objects.filter(user=request.user)

    ctx = {
        'profile': profile,
        'recent_progress': recent_progress,
        'upcoming_reminders': upcoming_reminders,
        'recent_interviews': recent_interviews,
        'announcements': announcements,
        'total_interviews': total_interviews,
        'avg_score': round(avg_score, 1),
        'total_chats': total_chats,
        'skills': skills,
    }
    return render(request, 'student/dashboard.html', ctx)


# ─── AI Chatbot ───────────────────────────────────────────────────────────────

@login_required
def chatbot(request):
    sessions = ChatSession.objects.filter(user=request.user)
    active_session = sessions.first()
    messages_list = []
    if active_session:
        messages_list = active_session.messages.all()
    return render(request, 'chatbot/chat.html', {
        'sessions': sessions, 'active_session': active_session,
        'messages_list': messages_list
    })


@login_required
def new_chat_session(request):
    if request.method == 'POST':
        category = request.POST.get('category', 'general')
        title = request.POST.get('title', 'New Chat')
        session = ChatSession.objects.create(user=request.user, title=title, category=category)
        return JsonResponse({'session_id': session.id, 'title': session.title})
    return JsonResponse({'error': 'POST required'}, status=400)


@login_required
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        session_id = data.get('session_id')
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'error': 'Empty message'}, status=400)

        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        
        # Save user message
        ChatMessage.objects.create(session=session, role='user', content=user_message)
        
        # Build history for API
        history = [{"role": m.role, "content": m.content} for m in session.messages.all()]
        
        # Get profile
        profile = getattr(request.user, 'student_profile', None)
        user_profile = None
        if profile:
            user_profile = {
                'name': request.user.get_full_name() or request.user.username,
                'skill_level': profile.skill_level,
                'target_role': profile.target_role,
                'subjects': profile.subjects,
            }
        
        try:
            response_text, tokens = chat_with_mentor(history, user_profile)
        except Exception as e:
            response_text = f"⚠️ AI service temporarily unavailable. Error: {str(e)[:100]}"
            tokens = 0
        
        # Save assistant message
        ai_msg = ChatMessage.objects.create(session=session, role='assistant',
                                             content=response_text, tokens_used=tokens)
        
        # Update session title if first message
        if session.messages.count() <= 2:
            session.title = user_message[:50] + ('...' if len(user_message) > 50 else '')
            session.save()
        
        # Track progress
        ProgressRecord.objects.create(user=request.user, activity_type='chat',
                                       activity_name=f'Chat: {session.title[:50]}', xp_earned=5)
        profile_obj, _ = StudentProfile.objects.get_or_create(user=request.user)
        profile_obj.total_xp += 5
        profile_obj.save()
        
        return JsonResponse({'message': response_text, 'timestamp': ai_msg.timestamp.strftime('%H:%M')})
    return JsonResponse({'error': 'POST required'}, status=400)


@login_required
def get_session_messages(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    msgs = [{'role': m.role, 'content': m.content, 'time': m.timestamp.strftime('%H:%M')}
            for m in session.messages.all()]
    return JsonResponse({'messages': msgs, 'title': session.title, 'category': session.category})


@login_required
def delete_chat_session(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.delete()
    return JsonResponse({'success': True})


# ─── Mock Interview ───────────────────────────────────────────────────────────

@login_required
def interview_list(request):
    interviews = MockInterview.objects.filter(user=request.user)
    return render(request, 'interview/list.html', {'interviews': interviews})


@login_required
def start_interview(request):
    if request.method == 'POST':
        domain = request.POST.get('domain', 'software_engineering')
        difficulty = request.POST.get('difficulty', 'medium')
        interview = MockInterview.objects.create(user=request.user, domain=domain,
                                                  difficulty=difficulty, status='in_progress')
        # Generate first question — always an introduction
        try:
            q_text, _ = generate_interview_question(domain, difficulty, 1)
        except Exception as e:
            q_text = f"Hello! Welcome to the interview. Can you please introduce yourself and tell me about your background in {domain.replace('_', ' ')}?"

        InterviewQuestion.objects.create(interview=interview, question_text=q_text, question_number=1)
        return redirect('interview_session', interview_id=interview.id)
    return render(request, 'interview/setup.html')


@login_required
def interview_session(request, interview_id):
    interview = get_object_or_404(MockInterview, id=interview_id, user=request.user)
    questions = interview.questions.all()
    current_q = questions.filter(user_answer='').first()
    return render(request, 'interview/session.html', {
        'interview': interview, 'questions': questions, 'current_question': current_q,
        'total_answered': questions.exclude(user_answer='').count(),
    })


@login_required
def submit_answer(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        interview_id = data.get('interview_id')
        question_id = data.get('question_id')
        answer = data.get('answer', '').strip()

        interview = get_object_or_404(MockInterview, id=interview_id, user=request.user)
        question = get_object_or_404(InterviewQuestion, id=question_id, interview=interview)

        if not answer:
            return JsonResponse({'error': 'Empty answer'}, status=400)

        question.user_answer = answer
        question.answered_at = timezone.now()

        # Evaluate answer
        try:
            eval_result, _ = evaluate_interview_answer(
                question.question_text, answer, interview.domain, interview.difficulty)
            question.score = eval_result.get('score', 5)
            question.feedback = eval_result.get('feedback', '')
            question.improvement_tips = json.dumps(eval_result.get('improvement_tips', []))
        except Exception as e:
            question.score = 5
            question.feedback = "Answer recorded. Evaluation unavailable."
            eval_result = {"score": 5, "grade": "Average", "strengths": [], "weaknesses": [],
                           "feedback": "Answer recorded.", "improvement_tips": [], "model_answer_hint": ""}

        question.save()

        # Generate next question (up to 7)
        answered_count = interview.questions.exclude(user_answer='').count()
        next_question = None

        # Fallback questions per slot — progressive from easy HR to technical
        fallback_questions = {
            2: f"What do you know about {interview.domain.replace('_', ' ')}? Explain the basics.",
            3: "Tell me about a challenging situation you faced and how you handled it.",
            4: f"Can you explain a key concept in {interview.domain.replace('_', ' ')} with an example?",
            5: f"Describe a project or task you worked on related to {interview.domain.replace('_', ' ')}.",
            6: f"What are the common challenges in {interview.domain.replace('_', ' ')} and how would you solve them?",
            7: "Where do you see yourself in the next 3-5 years? What are your career goals?",
        }

        if answered_count < 7:
            prev_qs = [q.question_text for q in interview.questions.all()]
            next_num = answered_count + 1
            try:
                next_q_text, _ = generate_interview_question(
                    interview.domain, interview.difficulty, next_num, prev_qs)
            except:
                next_q_text = fallback_questions.get(next_num, f"Can you tell me more about your experience in {interview.domain.replace('_', ' ')}?")

            next_obj = InterviewQuestion.objects.create(
                interview=interview, question_text=next_q_text, question_number=next_num)
            next_question = {'id': next_obj.id, 'text': next_q_text, 'number': next_obj.question_number}
        else:
            # Complete interview
            interview.status = 'completed'
            interview.completed_at = timezone.now()
            all_scores = [q.score for q in interview.questions.all() if q.score is not None]
            interview.overall_score = sum(all_scores) / len(all_scores) if all_scores else 0
            interview.save()

            # Award XP
            xp = int(interview.overall_score * 15)
            ProgressRecord.objects.create(user=request.user, activity_type='interview',
                                           activity_name=f'{interview.domain} Interview',
                                           score=interview.overall_score, xp_earned=xp,
                                           duration_minutes=interview.duration_minutes)
            profile, _ = StudentProfile.objects.get_or_create(user=request.user)
            profile.total_xp += xp
            profile.save()

        return JsonResponse({
            'success': True, 'score': question.score, 'evaluation': eval_result,
            'next_question': next_question, 'is_complete': interview.status == 'completed',
            'interview_id': interview.id
        })
    return JsonResponse({'error': 'POST required'}, status=400)


@login_required
def interview_result(request, interview_id):
    interview = get_object_or_404(MockInterview, id=interview_id, user=request.user)
    questions = interview.questions.all()
    for q in questions:
        try:
            q.tips_list = json.loads(q.improvement_tips) if q.improvement_tips else []
        except:
            q.tips_list = []
    return render(request, 'interview/result.html', {'interview': interview, 'questions': questions})


# ─── Reminders ────────────────────────────────────────────────────────────────

@login_required
def reminders(request):
    if request.method == 'POST':
        Reminder.objects.create(
            user=request.user,
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            reminder_type=request.POST.get('reminder_type', 'study'),
            priority=request.POST.get('priority', 'medium'),
            due_datetime=request.POST.get('due_datetime'),
            repeat=request.POST.get('repeat', 'none'),
        )
        messages.success(request, 'Reminder created successfully!')
        return redirect('reminders')

    all_reminders = Reminder.objects.filter(user=request.user, is_active=True)
    pending = all_reminders.filter(is_completed=False)
    completed = all_reminders.filter(is_completed=True)[:10]
    return render(request, 'reminders/reminders.html', {
        'pending_reminders': pending, 'completed_reminders': completed
    })


@login_required
def complete_reminder(request, reminder_id):
    reminder = get_object_or_404(Reminder, id=reminder_id, user=request.user)
    reminder.is_completed = True
    reminder.save()
    return JsonResponse({'success': True})


@login_required
def delete_reminder(request, reminder_id):
    reminder = get_object_or_404(Reminder, id=reminder_id, user=request.user)
    reminder.delete()
    return JsonResponse({'success': True})


# ─── Progress Tracking ────────────────────────────────────────────────────────

@login_required
def progress(request):
    records = ProgressRecord.objects.filter(user=request.user)
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    skills = SkillAssessment.objects.filter(user=request.user)

    # Chart data
    from collections import defaultdict
    daily_xp = defaultdict(int)
    for r in records.filter(recorded_at__gte=timezone.now() - timezone.timedelta(days=30)):
        day = r.recorded_at.strftime('%Y-%m-%d')
        daily_xp[day] += r.xp_earned

    chart_labels = sorted(daily_xp.keys())[-14:]
    chart_data = [daily_xp[d] for d in chart_labels]

    activity_counts = records.values('activity_type').annotate(count=Count('id'))
    
    ctx = {
        'records': records[:20], 'profile': profile, 'skills': skills,
        'chart_labels': json.dumps(chart_labels), 'chart_data': json.dumps(chart_data),
        'activity_counts': list(activity_counts),
        'total_xp': records.aggregate(Sum('xp_earned'))['xp_earned__sum'] or 0,
        'total_activities': records.count(),
    }
    return render(request, 'progress/progress.html', ctx)


@login_required
def update_skill(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        skill, _ = SkillAssessment.objects.get_or_create(user=request.user, skill_name=data['skill'])
        skill.score = data.get('score', 0)
        skill.save()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'POST required'}, status=400)


# ─── Personalized Suggestions ─────────────────────────────────────────────────

@login_required
def suggestions(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    skills = SkillAssessment.objects.filter(user=request.user)
    interviews = MockInterview.objects.filter(user=request.user, status='completed')

    user_data = {
        'name': request.user.get_full_name() or request.user.username,
        'skill_level': profile.skill_level,
        'target_role': profile.target_role,
        'subjects': profile.subjects,
        'total_xp': profile.total_xp,
        'level': profile.level,
        'completed_interviews': interviews.count(),
        'avg_interview_score': interviews.aggregate(Avg('overall_score'))['overall_score__avg'] or 0,
        'skills': {s.skill_name: s.score for s in skills},
    }

    suggestion_data = None
    error = None
    try:
        suggestion_data, _ = generate_personalized_suggestions(user_data)
    except Exception as e:
        error = str(e)

    return render(request, 'student/suggestions.html', {
        'suggestion_data': suggestion_data, 'profile': profile, 'error': error
    })


# ─── Admin Dashboard ──────────────────────────────────────────────────────────

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    total_students = User.objects.filter(is_staff=False).count()
    total_interviews = MockInterview.objects.count()
    total_chats = ChatMessage.objects.count()
    recent_users = User.objects.filter(is_staff=False).order_by('-date_joined')[:10]
    recent_interviews = MockInterview.objects.select_related('user').order_by('-started_at')[:10]
    announcements = Announcement.objects.all()[:5]

    ctx = {
        'total_students': total_students,
        'total_interviews': total_interviews,
        'total_chats': total_chats,
        'recent_users': recent_users,
        'recent_interviews': recent_interviews,
        'announcements': announcements,
    }
    return render(request, 'admin_dash/dashboard.html', ctx)


@login_required
def admin_students(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    students = User.objects.filter(is_staff=False).select_related('student_profile').order_by('-date_joined')
    return render(request, 'admin_dash/students.html', {'students': students})


@login_required
def admin_student_detail(request, user_id):
    if not request.user.is_staff:
        return redirect('dashboard')
    student = get_object_or_404(User, id=user_id, is_staff=False)
    profile, _ = StudentProfile.objects.get_or_create(user=student)
    interviews = MockInterview.objects.filter(user=student).order_by('-started_at')
    progress_records = ProgressRecord.objects.filter(user=student)[:20]
    skills = SkillAssessment.objects.filter(user=student)
    return render(request, 'admin_dash/student_detail.html', {
        'student': student, 'profile': profile, 'interviews': interviews,
        'progress_records': progress_records, 'skills': skills
    })


@login_required
def create_announcement(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    if request.method == 'POST':
        Announcement.objects.create(
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            announcement_type=request.POST.get('announcement_type', 'info'),
            created_by=request.user,
        )
        messages.success(request, 'Announcement posted!')
    return redirect('admin_dashboard')


@login_required
def admin_analytics(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    
    from collections import defaultdict
    from django.db.models.functions import TruncDate
    
    # Daily registrations last 30 days
    regs = (User.objects.filter(is_staff=False, date_joined__gte=timezone.now()-timezone.timedelta(days=30))
            .extra({'day': "date(date_joined)"}).values('day').annotate(count=Count('id')).order_by('day'))

    interview_by_domain = (MockInterview.objects.values('domain')
                           .annotate(count=Count('id'), avg_score=Avg('overall_score')))

    ctx = {
        'reg_labels': json.dumps([r['day'] for r in regs]),
        'reg_data': json.dumps([r['count'] for r in regs]),
        'interview_domains': list(interview_by_domain),
    }
    return render(request, 'admin_dash/analytics.html', ctx)


@login_required
def profile_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        profile.bio = request.POST.get('bio', '')
        profile.skill_level = request.POST.get('skill_level', 'beginner')
        profile.target_role = request.POST.get('target_role', '')
        profile.subjects = request.POST.get('subjects', '')
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    return render(request, 'student/profile.html', {'profile': profile})