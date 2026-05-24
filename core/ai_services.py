import json
import os
from django.conf import settings

# ─── Use the same groq library as your working Streamlit main.py ─────────────
from groq import Groq


def _get_client():
    """Create Groq client exactly like main.py does."""
    api_key = getattr(settings, 'GROQ_API_KEY', '') or os.getenv('GROQ_API_KEY', '')
    if not api_key or api_key in ('your-groq-api-key-here', 'PASTE_YOUR_NEW_GROQ_KEY_HERE'):
        raise Exception(
            "Groq API key not set! Open ai_mentor/settings.py and set GROQ_API_KEY."
        )
    return Groq(api_key=api_key)


def call_groq(messages, system_prompt=None, model="llama-3.1-8b-instant", temperature=0.7, max_tokens=1024):
    """
    Call Groq API using the official groq SDK — same as your working Streamlit main.py.
    Model: llama-3.1-8b-instant  ✅ (confirmed working in your Streamlit)
    """
    client = _get_client()

    formatted_messages = []
    if system_prompt:
        formatted_messages.append({"role": "system", "content": system_prompt})
    formatted_messages.extend(messages)

    try:
        # Exact same call as main.py's _response() method
        completion = client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            stop=None,
        )
        content = completion.choices[0].message.content
        tokens = completion.usage.total_tokens if completion.usage else 0
        return content, tokens

    except Exception as e:
        error_str = str(e)
        if '401' in error_str:
            raise Exception("Invalid Groq API Key (401). Get a new key at https://console.groq.com/keys")
        elif '403' in error_str:
            raise Exception(f"Groq Access Denied (403). Check your API key. Detail: {error_str[:200]}")
        elif '429' in error_str:
            raise Exception("Groq Rate Limit (429). Wait 1 minute and try again.")
        elif '404' in error_str:
            raise Exception(f"Model not found (404). Detail: {error_str[:200]}")
        else:
            raise Exception(f"Groq Error: {error_str[:300]}")


# ─── All AI feature functions below ──────────────────────────────────────────

def get_academic_answer(question, subject="general", level="undergraduate"):
    system = f"""You are an expert academic tutor specializing in {subject} for {level} students.
Provide clear, detailed, and educational answers. Use examples, analogies, and step-by-step explanations.
Format your response with proper structure using markdown. Include:
- Clear explanation
- Examples where appropriate
- Key points to remember
- Related concepts to explore"""
    messages = [{"role": "user", "content": question}]
    return call_groq(messages, system_prompt=system, max_tokens=1500)


def generate_interview_question(domain, difficulty, question_number, previous_questions=None):
    """
    Generate interview questions in a structured, progressive order:
    Q1 - Self Introduction (always easy, conversational)
    Q2 - Basic concept (fundamental knowledge)
    Q3 - HR / Behavioral (STAR method)
    Q4 - Intermediate technical
    Q5 - Problem solving / scenario
    Q6 - Advanced technical (based on difficulty)
    Q7 - Career goals / closing HR question
    """
    prev_q = "\n".join(previous_questions) if previous_questions else "None yet"

    # Define question type based on question number
    question_type_map = {
        1: "SELF INTRODUCTION — Ask the candidate to introduce themselves, their background, and what they know about the domain. Keep it friendly and conversational. Example: 'Tell me about yourself and your interest in {domain}.'",
        2: "BASIC CONCEPT — Ask a simple, fundamental concept question about {domain}. Something a fresher would know. Example: 'What is object-oriented programming?' or 'What is a database?'",
        3: "HR / BEHAVIORAL — Ask a behavioral question using STAR method. Example: 'Tell me about a time you faced a challenge and how you solved it.' or 'Describe a project you are proud of.'",
        4: "INTERMEDIATE TECHNICAL — Ask a moderate technical question about {domain}. Not too hard, real-world focused. Example: 'How would you design a simple REST API?' or 'Explain the difference between supervised and unsupervised learning.'",
        5: "PRACTICAL SCENARIO — Give a simple real-world scenario relevant to {domain}. Example: 'Your website is loading slowly, what would you do?' or 'How would you handle duplicate data in a dataset?'",
        6: "SLIGHTLY ADVANCED TECHNICAL — Ask a more advanced question suitable for {difficulty} level. But keep it reasonable and answerable. Example: 'Explain how you would optimize a slow database query.' or 'What is overfitting in machine learning and how do you prevent it?'",
        7: "CLOSING HR — Ask a motivational or career-focused question. Example: 'Where do you see yourself in 5 years?' or 'Why do you want to work in {domain}?' or 'What are your greatest strengths?'"
    }

    q_type = question_type_map.get(question_number, question_type_map[4])
    q_type = q_type.replace('{domain}', domain.replace('_', ' ')).replace('{difficulty}', difficulty)

    system = f"""You are a friendly HR and technical interviewer conducting a structured job interview.
Domain: {domain.replace('_', ' ')}, Difficulty: {difficulty}
Question number: {question_number} out of 7

YOUR TASK FOR THIS QUESTION:
{q_type}

IMPORTANT RULES:
- Generate ONE clear, concise question
- Do NOT make it overly complex or multi-part
- Do NOT repeat any previous questions
- Keep it conversational and human-like
- For question 1-3: keep it simple and friendly
- For question 4-6: be technical but not impossibly hard
- Return ONLY the question text, nothing else

Previous questions asked (DO NOT REPEAT):
{prev_q}"""

    messages = [{"role": "user", "content": f"Generate question #{question_number} for {domain.replace('_', ' ')} interview"}]
    response, tokens = call_groq(messages, system_prompt=system, max_tokens=200, temperature=0.7)
    return response.strip(), tokens


def evaluate_interview_answer(question, answer, domain, difficulty):
    system = f"""You are an expert technical interviewer evaluating a candidate's answer.
Domain: {domain}, Difficulty: {difficulty}
Evaluate and respond in this EXACT JSON format:
{{
  "score": <0-10 integer>,
  "grade": "<Excellent/Good/Average/Poor>",
  "strengths": ["point1", "point2"],
  "weaknesses": ["point1", "point2"],
  "feedback": "<2-3 sentence feedback>",
  "improvement_tips": ["tip1", "tip2", "tip3"],
  "model_answer_hint": "<brief hint at ideal answer>",
  "keywords_missed": ["keyword1", "keyword2"]
}}
Return ONLY valid JSON, no markdown, no extra text."""
    messages = [{"role": "user", "content": f"Question: {question}\n\nCandidate's Answer: {answer}"}]
    response, tokens = call_groq(messages, system_prompt=system, max_tokens=800, temperature=0.3)
    try:
        clean = response.strip()
        if '```' in clean:
            parts = clean.split('```')
            for part in parts:
                part = part.strip()
                if part.startswith('json'):
                    part = part[4:].strip()
                if part.startswith('{'):
                    clean = part
                    break
        result = json.loads(clean)
    except Exception:
        result = {
            "score": 5, "grade": "Average",
            "strengths": ["Attempted the question"],
            "weaknesses": ["Answer needs more depth"],
            "feedback": response[:200] if response else "Could not evaluate answer.",
            "improvement_tips": ["Be more specific", "Use real examples", "Structure your answer clearly"],
            "model_answer_hint": "Review the core concepts of this topic.",
            "keywords_missed": []
        }
    return result, tokens


def generate_personalized_suggestions(user_data):
    system = """You are a career and academic advisor. Based on the student profile, provide personalized suggestions.
Return ONLY valid JSON (no markdown, no extra text):
{
  "priority_skills": ["skill1", "skill2", "skill3"],
  "study_plan": [{"day": 1, "task": "task description", "duration": "2 hours"}],
  "resources": [{"title": "name", "type": "book/video/course", "url_hint": "website.com"}],
  "weekly_goals": ["goal1", "goal2", "goal3"],
  "motivational_message": "encouraging message",
  "estimated_readiness": 65
}
Keep study_plan to 5 days max. Keep resources to 4 items max."""
    messages = [{"role": "user", "content": f"Student profile: {json.dumps(user_data)}"}]
    response, tokens = call_groq(messages, system_prompt=system, max_tokens=1200, temperature=0.7)
    try:
        clean = response.strip()
        if '```' in clean:
            parts = clean.split('```')
            for part in parts:
                part = part.strip()
                if part.startswith('json'):
                    part = part[4:].strip()
                if part.startswith('{'):
                    clean = part
                    break
        return json.loads(clean), tokens
    except Exception:
        return {
            "priority_skills": ["Python", "Data Structures", "System Design"],
            "study_plan": [
                {"day": 1, "task": "Review Python fundamentals and OOP", "duration": "2 hours"},
                {"day": 2, "task": "Practice data structures: Arrays, Linked Lists", "duration": "2 hours"},
                {"day": 3, "task": "Study system design basics", "duration": "1.5 hours"},
                {"day": 4, "task": "Mock interview practice", "duration": "1 hour"},
                {"day": 5, "task": "Solve 5 coding problems on LeetCode", "duration": "2 hours"},
            ],
            "resources": [
                {"title": "Python Official Docs", "type": "docs", "url_hint": "docs.python.org"},
                {"title": "CS50 by Harvard", "type": "course", "url_hint": "cs50.harvard.edu"},
                {"title": "LeetCode", "type": "practice", "url_hint": "leetcode.com"},
                {"title": "System Design Primer", "type": "github", "url_hint": "github.com/donnemartin"},
            ],
            "weekly_goals": ["Complete 3 mock interviews", "Study 2 hours daily", "Solve 5 coding problems"],
            "motivational_message": "Consistency is the key to success. Keep going!",
            "estimated_readiness": 60
        }, tokens


def chat_with_mentor(messages_history, user_profile=None):
    profile_context = ""
    if user_profile:
        profile_context = f"""Student: {user_profile.get('name', 'Student')}
Level: {user_profile.get('skill_level', 'beginner')}
Target Role: {user_profile.get('target_role', 'Software Engineer')}
Subjects: {user_profile.get('subjects', 'Computer Science')}"""

    system = f"""You are EduBot - an advanced AI Academic Mentor and Career Coach for students.
{profile_context}
Your capabilities:
- Answer academic questions across all subjects with detailed explanations
- Provide interview preparation guidance and tips
- Offer career counseling and skill gap analysis
- Create personalized study plans
- Motivate and support students
Guidelines:
- Be friendly, encouraging, and educational
- Use emojis appropriately
- Format responses with markdown when helpful
- Always encourage the student"""

    return call_groq(messages_history, system_prompt=system, max_tokens=1200)


def test_groq_connection():
    """
    Test from Django shell:
      python manage.py shell
      from core.ai_services import test_groq_connection
      test_groq_connection()
    """
    try:
        response, tokens = call_groq(
            [{"role": "user", "content": "Say 'Groq works!' and nothing else."}],
            max_tokens=10
        )
        print(f"✅ SUCCESS! Response: {response} | Tokens: {tokens}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False