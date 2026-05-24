from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class StudentProfile(models.Model):
    SKILL_LEVELS = [('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    bio = models.TextField(blank=True)
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVELS, default='beginner')
    target_role = models.CharField(max_length=100, blank=True)
    subjects = models.TextField(blank=True, help_text="Comma-separated subjects")
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_xp = models.IntegerField(default=0)
    streak_days = models.IntegerField(default=0)
    last_active = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def level(self):
        if self.total_xp < 500: return 1
        elif self.total_xp < 1500: return 2
        elif self.total_xp < 3000: return 3
        elif self.total_xp < 5000: return 4
        else: return 5

    @property
    def level_name(self):
        names = {1: 'Novice', 2: 'Explorer', 3: 'Scholar', 4: 'Expert', 5: 'Master'}
        return names[self.level]


class ChatSession(models.Model):
    CATEGORIES = [
        ('academic', 'Academic Query'),
        ('interview_prep', 'Interview Preparation'),
        ('career', 'Career Guidance'),
        ('general', 'General'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=200, default='New Chat')
    category = models.CharField(max_length=30, choices=CATEGORIES, default='general')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class ChatMessage(models.Model):
    ROLES = [('user', 'User'), ('assistant', 'Assistant')]
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    tokens_used = models.IntegerField(default=0)

    class Meta:
        ordering = ['timestamp']


class MockInterview(models.Model):
    DOMAINS = [
        ('software_engineering', 'Software Engineering'),
        ('data_science', 'Data Science'),
        ('web_development', 'Web Development'),
        ('machine_learning', 'Machine Learning'),
        ('system_design', 'System Design'),
        ('behavioral', 'Behavioral'),
        ('hr', 'HR Round'),
    ]
    DIFFICULTY = [('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')]
    STATUS = [('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interviews')
    domain = models.CharField(max_length=50, choices=DOMAINS)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY, default='medium')
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    overall_score = models.FloatField(null=True, blank=True)
    feedback_summary = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=0)

    class Meta:
        ordering = ['-started_at']


class InterviewQuestion(models.Model):
    interview = models.ForeignKey(MockInterview, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_number = models.IntegerField()
    expected_answer = models.TextField(blank=True)
    user_answer = models.TextField(blank=True)
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    improvement_tips = models.TextField(blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['question_number']


class Reminder(models.Model):
    TYPES = [
        ('study', 'Study Session'),
        ('interview_practice', 'Interview Practice'),
        ('assignment', 'Assignment Deadline'),
        ('revision', 'Revision'),
        ('custom', 'Custom'),
    ]
    PRIORITY = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]
    REPEAT = [('none', 'No Repeat'), ('daily', 'Daily'), ('weekly', 'Weekly')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    reminder_type = models.CharField(max_length=30, choices=TYPES, default='study')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='medium')
    due_datetime = models.DateTimeField()
    repeat = models.CharField(max_length=10, choices=REPEAT, default='none')
    is_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_datetime']

    @property
    def is_overdue(self):
        return not self.is_completed and self.due_datetime < timezone.now()


class ProgressRecord(models.Model):
    ACTIVITY_TYPES = [
        ('chat', 'AI Chat'),
        ('interview', 'Mock Interview'),
        ('study', 'Study Session'),
        ('quiz', 'Quiz Completed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    activity_name = models.CharField(max_length=200)
    score = models.FloatField(null=True, blank=True)
    xp_earned = models.IntegerField(default=0)
    duration_minutes = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']


class SkillAssessment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skill_assessments')
    skill_name = models.CharField(max_length=100)
    score = models.IntegerField(default=0)  # 0-100
    assessed_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['user', 'skill_name']
        ordering = ['-score']


class Announcement(models.Model):
    TYPES = [('info', 'Info'), ('warning', 'Warning'), ('success', 'Success')]
    title = models.CharField(max_length=200)
    content = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=TYPES, default='info')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    target_all = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
