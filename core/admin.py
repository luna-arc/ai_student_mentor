from django.contrib import admin
from .models import (StudentProfile, ChatSession, ChatMessage, MockInterview,
                     InterviewQuestion, Reminder, ProgressRecord, SkillAssessment, Announcement)

admin.site.register(StudentProfile)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)
admin.site.register(MockInterview)
admin.site.register(InterviewQuestion)
admin.site.register(Reminder)
admin.site.register(ProgressRecord)
admin.site.register(SkillAssessment)
admin.site.register(Announcement)
