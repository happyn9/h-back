"""
Templates de rappel quotidien (7h30) — email + push, en français et en anglais.

Deux scénarios :
- subscribed_*   : l'utilisateur a un abonnement actif -> on l'encourage à continuer.
- unsubscribed_* : l'utilisateur n'a pas d'abonnement actif -> on l'encourage à s'inscrire.

Chaque fonction *_email retourne un tuple (subject, html_content).
Chaque fonction *_push retourne un tuple (title, body).
"""

from app.utils.send_email import _base_template, BASE_URL

SUPPORTED_LANGUAGES = ("en", "fr")


def _normalize_lang(lang: str) -> str:
    lang = (lang or "en").lower()
    return lang if lang in SUPPORTED_LANGUAGES else "en"


# -------------------------------
# Utilisateur ABONNÉ : rappel à continuer
# -------------------------------
def subscribed_reminder_email(lang: str, name: str) -> tuple[str, str]:
    lang = _normalize_lang(lang)

    if lang == "fr":
        subject = "☀️ Ton créneau d'apprentissage t'attend"
        body = f"""
        <p>Salut {name},</p>
        <p>Il est 7h30 — le moment parfait pour avancer un peu sur ton cours
           avant que la journée ne s'emballe.</p>
        <p>Même 10 minutes aujourd'hui te rapprochent de ton objectif. 💪</p>
        """
        html = _base_template(
            title="Prêt à apprendre aujourd'hui ?",
            body_html=body,
            button_label="Continuer mon cours",
            button_url=f"{BASE_URL}/courses",
        )
    else:
        subject = "☀️ Your learning slot is ready"
        body = f"""
        <p>Hey {name},</p>
        <p>It's 7:30 AM — the perfect time to make a little progress before
           the day gets busy.</p>
        <p>Even 10 minutes today gets you closer to your goal. 💪</p>
        """
        html = _base_template(
            title="Ready to learn today?",
            body_html=body,
            button_label="Continue my course",
            button_url=f"{BASE_URL}/courses",
        )

    return subject, html


def subscribed_reminder_push(lang: str, name: str) -> tuple[str, str]:
    lang = _normalize_lang(lang)

    if lang == "fr":
        return (
            "C'est l'heure d'apprendre ☀️",
            f"{name}, ton cours t'attend. 10 minutes suffisent pour avancer aujourd'hui.",
        )
    return (
        "Time to learn ☀️",
        f"{name}, your course is waiting. 10 minutes is all it takes today.",
    )


# -------------------------------
# Utilisateur NON ABONNÉ : encouragement à s'inscrire
# -------------------------------
def unsubscribed_reminder_email(lang: str, name: str) -> tuple[str, str]:
    lang = _normalize_lang(lang)

    if lang == "fr":
        subject = "☀️ Et si aujourd'hui était le bon jour ?"
        body = f"""
        <p>Salut {name},</p>
        <p>Chaque matin est une nouvelle occasion de commencer quelque chose
           qui compte vraiment pour toi.</p>
        <p>Découvre nos cours et choisis celui qui te fera avancer, dès aujourd'hui.</p>
        """
        html = _base_template(
            title="Commence ton apprentissage aujourd'hui",
            body_html=body,
            button_label="Découvrir les cours",
            button_url=f"{BASE_URL}/courses",
        )
    else:
        subject = "☀️ What if today was the day?"
        body = f"""
        <p>Hey {name},</p>
        <p>Every morning is a new chance to start something that actually
           matters to you.</p>
        <p>Check out our courses and pick the one that moves you forward,
           starting today.</p>
        """
        html = _base_template(
            title="Start learning today",
            body_html=body,
            button_label="Explore courses",
            button_url=f"{BASE_URL}/courses",
        )

    return subject, html


def unsubscribed_reminder_push(lang: str, name: str) -> tuple[str, str]:
    lang = _normalize_lang(lang)

    if lang == "fr":
        return (
            "Prêt à commencer ? ☀️",
            f"{name}, tes cours t'attendent. Fais le premier pas aujourd'hui.",
        )
    return (
        "Ready to start? ☀️",
        f"{name}, your courses are waiting. Take the first step today.",
    )