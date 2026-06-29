# scripts/seed_subscriptions.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.subscription import Subscription

db = SessionLocal()

# Récupère les course_id existants d'abord
from app.models.course import Course
courses = db.query(Course).all()
print(f"Cours trouvés: {[(c.id, c.title) for c in courses]}")

# Crée un plan monthly + yearly pour chaque cours
subs = []
for course in courses:
    subs.append(Subscription(
        name=f"{course.title} — Monthly",
        description=f"Accès mensuel à {course.title}",
        duration_days=30,
        price=course.standard_price or 99.0,
        billing_type="monthly",
        course_id=course.id,
        has_ai_assistant=False,
    ))
    subs.append(Subscription(
        name=f"{course.title} — Yearly",
        description=f"Accès annuel à {course.title}",
        duration_days=365,
        price=course.premium_price or 999.0,
        billing_type="yearly",
        course_id=course.id,
        has_ai_assistant=True,
        ai_monthly_question_limit=100,
    ))

db.add_all(subs)
db.commit()
print(f"✅ {len(subs)} subscriptions créées")
db.close()