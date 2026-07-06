
import logging
from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.core.config import settings

logger = logging.getLogger("hlearning.email")

# -------------------------------
# Constantes de design
# -------------------------------
BRAND_COLOR = "#2B0A5B"
BRAND_COLOR_DARK = "#1A0638"
BRAND_ACCENT = "#7C3AED"
BRAND_COLOR_LIGHT = "#F4F1FA"
TEXT_COLOR = "#1F1F2E"
MUTED_COLOR = "#6B6B7B"
BASE_URL = "https://h-learning-wine.vercel.app"
DEFAULT_FROM_EMAIL = "hlearningsarl@gmail.com"

SUPPORTED_LANGUAGES = ("en", "fr")


def _normalize_lang(lang: Optional[str]) -> str:
    lang = (lang or "en").lower()
    return lang if lang in SUPPORTED_LANGUAGES else "en"


# -------------------------------
# Envoi d'email (SendGrid)
# -------------------------------
def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    from_email: str = DEFAULT_FROM_EMAIL,
) -> bool:
    """
    Envoie un email via SendGrid. Retourne True/False, ne lève jamais
    d'exception (loggée uniquement) pour ne pas casser le flux appelant.
    """
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
    )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info("Email envoyé à %s | statut: %s", to_email, response.status_code)
        return True
    except Exception:
        logger.exception("Échec de l'envoi de l'email à %s", to_email)
        return False


# -------------------------------
# Template de base "premium"
# -------------------------------
def _base_template(
    title: str,
    body_html: str,
    button_label: Optional[str] = None,
    button_url: Optional[str] = None,
    eyebrow: Optional[str] = None,
) -> str:
    """
    Enveloppe commune : header en dégradé violet, carte blanche avec ombre
    portée, badge "eyebrow" optionnel au-dessus du titre, bouton en dégradé.
    Styles 100% inline pour compatibilité avec les clients mail.
    """
    eyebrow_block = ""
    if eyebrow:
        eyebrow_block = f"""
        <tr>
          <td style="padding-bottom:14px;">
            <span style="background-color:{BRAND_COLOR_LIGHT}; color:{BRAND_COLOR};
                         font-size:11px; font-weight:700; letter-spacing:1px;
                         text-transform:uppercase; padding:6px 14px; border-radius:20px;
                         display:inline-block;">
              {eyebrow}
            </span>
          </td>
        </tr>
        """

    button_block = ""
    if button_label and button_url:
        button_block = f"""
        <tr>
          <td align="center" style="padding: 32px 0 8px 0;">
            <a href="{button_url}"
               style="background: linear-gradient(135deg, {BRAND_COLOR} 0%, {BRAND_ACCENT} 100%);
                      color:#ffffff; text-decoration:none; padding:16px 40px; border-radius:10px;
                      font-weight:700; font-size:15px; display:inline-block;
                      box-shadow: 0 6px 16px rgba(124,58,237,0.35);">
              {button_label}
            </a>
          </td>
        </tr>
        """

    return f"""\
<html>
  <body style="margin:0; padding:0; background-color:#EEEAF6; font-family:'Segoe UI', Roboto, Arial, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="padding: 40px 16px;">
      <tr>
        <td align="center">
          <table width="520" cellpadding="0" cellspacing="0"
                 style="background-color:#ffffff; border-radius:16px; overflow:hidden;
                        box-shadow: 0 8px 30px rgba(43,10,91,0.15);">

            <!-- Header dégradé -->
            <tr>
              <td style="background: linear-gradient(135deg, {BRAND_COLOR_DARK} 0%, {BRAND_COLOR} 55%, {BRAND_ACCENT} 100%);
                         padding: 36px 40px;">
                <span style="color:#ffffff; font-size:22px; font-weight:800; letter-spacing:0.5px;">
                  H-Learning
                </span>
                <div style="color:rgba(255,255,255,0.75); font-size:12px; margin-top:4px; letter-spacing:0.5px;">
                  Apprendre. Progresser. Réussir.
                </div>
              </td>
            </tr>

            <!-- Body -->
            <tr>
              <td style="padding: 40px;">
                <table width="100%" cellpadding="0" cellspacing="0">
                  {eyebrow_block}
                  <tr>
                    <td style="color:{TEXT_COLOR}; font-size:15px; line-height:1.7;">
                      <h2 style="margin:0 0 18px 0; color:{BRAND_COLOR_DARK}; font-size:22px; font-weight:800;">
                        {title}
                      </h2>
                      {body_html}
                    </td>
                  </tr>
                  {button_block}
                </table>
              </td>
            </tr>

            <!-- Divider -->
            <tr>
              <td style="padding: 0 40px;">
                <div style="border-top:1px solid #EDEAF4;"></div>
              </td>
            </tr>

            <!-- Footer -->
            <tr>
              <td style="padding: 24px 40px 32px 40px; text-align:center;">
                <span style="color:{MUTED_COLOR}; font-size:12px; line-height:1.6;">
                  © H-Learning — Cet email a été envoyé automatiquement, merci de ne pas y répondre.<br/>
                  <a href="{BASE_URL}" style="color:{BRAND_ACCENT}; text-decoration:none;">h-learning-wine.vercel.app</a>
                </span>
              </td>
            </tr>

          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


# -------------------------------
# Templates transactionnels (FR/EN)
# -------------------------------
def welcome_email(name: str, lang: str = "en") -> tuple[str, str]:
    lang = _normalize_lang(lang)

    if lang == "fr":
        subject = f"Bienvenue sur H-Learning, {name} !"
        body = f"""
        <p>Bienvenue <strong>{name}</strong> 👋</p>
        <p>Merci de rejoindre H-Learning. Explore dès maintenant nos cours
           premium et commence ton apprentissage.</p>
        """
        html = _base_template(
            title=f"Bienvenue, {name} !",
            body_html=body,
            button_label="Se connecter",
            button_url=f"{BASE_URL}/auth",
            eyebrow="Bienvenue",
        )
    else:
        subject = f"Welcome to H-Learning, {name}!"
        body = f"""
        <p>Welcome <strong>{name}</strong> 👋</p>
        <p>Thanks for joining H-Learning. Explore our premium courses and
           start learning today.</p>
        """
        html = _base_template(
            title=f"Welcome, {name}!",
            body_html=body,
            button_label="Log in now",
            button_url=f"{BASE_URL}/auth",
            eyebrow="Welcome",
        )

    return subject, html


def login_alert_email(name: str, ip_address: str, lang: str = "en") -> tuple[str, str]:
    lang = _normalize_lang(lang)

    if lang == "fr":
        subject = "Alerte de connexion à ton compte"
        body = f"""
        <p>Bonjour {name},</p>
        <p>Nous avons détecté une connexion à ton compte depuis l'adresse IP
           <strong>{ip_address}</strong>.</p>
        <p>Si c'est bien toi, aucune action n'est nécessaire. Sinon, sécurise
           ton compte immédiatement.</p>
        """
        html = _base_template(
            title="Alerte de connexion",
            body_html=body,
            button_label="Sécuriser mon compte",
            button_url=f"{BASE_URL}/security",
            eyebrow="Sécurité",
        )
    else:
        subject = "New login to your account"
        body = f"""
        <p>Hello {name},</p>
        <p>We noticed a login to your account from IP address
           <strong>{ip_address}</strong>.</p>
        <p>If this was you, no action is needed. Otherwise, please secure
           your account immediately.</p>
        """
        html = _base_template(
            title="Login alert",
            body_html=body,
            button_label="Secure my account",
            button_url=f"{BASE_URL}/security",
            eyebrow="Security",
        )

    return subject, html


def otp_email(otp_code: str, lang: str = "en") -> tuple[str, str]:
    lang = _normalize_lang(lang)

    code_block = f"""
    <div style="text-align:center; margin: 24px 0;">
      <span style="background-color:{BRAND_COLOR_LIGHT}; color:{BRAND_COLOR};
                   font-size:30px; font-weight:800; letter-spacing:8px;
                   padding:16px 28px; border-radius:12px; display:inline-block;">
        {otp_code}
      </span>
    </div>
    """

    if lang == "fr":
        subject = "Ton code de vérification H-Learning"
        body = f"""
        <p>Utilise le code ci-dessous pour vérifier ton compte :</p>
        {code_block}
        <p style="color:{MUTED_COLOR}; font-size:13px;">Ce code expire dans 5 minutes.</p>
        """
        html = _base_template(title="Code de vérification", body_html=body, eyebrow="Vérification")
    else:
        subject = "Your H-Learning verification code"
        body = f"""
        <p>Use the code below to verify your account:</p>
        {code_block}
        <p style="color:{MUTED_COLOR}; font-size:13px;">This code expires in 5 minutes.</p>
        """
        html = _base_template(title="Verification code", body_html=body, eyebrow="Verification")

    return subject, html


def subscription_email(course_name: str, lang: str = "en") -> tuple[str, str]:
    lang = _normalize_lang(lang)
    slug = course_name.replace(" ", "-").lower()

    if lang == "fr":
        subject = "Abonnement confirmé !"
        body = f"""
        <p>Ton abonnement à <strong>{course_name}</strong> est confirmé 🎉</p>
        <p>Commence à apprendre dès maintenant et développe ton plein potentiel.</p>
        """
        html = _base_template(
            title="Abonnement confirmé !",
            body_html=body,
            button_label="Accéder au cours",
            button_url=f"{BASE_URL}/{slug}",
            eyebrow="Abonnement",
        )
    else:
        subject = "Subscription confirmed!"
        body = f"""
        <p>Your subscription to <strong>{course_name}</strong> is confirmed 🎉</p>
        <p>Start learning now and unlock your full potential.</p>
        """
        html = _base_template(
            title="Subscription confirmed!",
            body_html=body,
            button_label="Go to course",
            button_url=f"{BASE_URL}/{slug}",
            eyebrow="Subscription",
        )

    return subject, html


# Traduction des statuts les plus courants ; les valeurs inconnues sont
# affichées telles quelles (fallback).
_STATUS_LABELS = {
    "en": {"approved": "approved", "rejected": "rejected", "pending": "pending"},
    "fr": {"approved": "approuvée", "rejected": "rejetée", "pending": "en attente"},
}


def request_response_email(request_title: str, status: str, lang: str = "en") -> tuple[str, str]:
    lang = _normalize_lang(lang)
    status_key = (status or "").strip().lower()
    display_status = _STATUS_LABELS.get(lang, _STATUS_LABELS["en"]).get(status_key, status)

    if lang == "fr":
        subject = "Mise à jour de ta demande"
        body = f"""
        <p>Ta demande <strong>{request_title}</strong> a été
           <strong>{display_status}</strong>.</p>
        <p>Merci d'utiliser H-Learning !</p>
        """
        html = _base_template(title="Mise à jour de ta demande", body_html=body, eyebrow="Demande")
    else:
        subject = "Update on your request"
        body = f"""
        <p>Your request <strong>{request_title}</strong> has been
           <strong>{display_status}</strong>.</p>
        <p>Thank you for using H-Learning!</p>
        """
        html = _base_template(title="Update on your request", body_html=body, eyebrow="Request")

    return subject, html


# -------------------------------
# Exemple d'utilisation
# -------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Anglais
    subj, html = welcome_email("John", lang="en")
    send_email("user@example.com", subj, html)

    # Français
    subj, html = welcome_email("Jean", lang="fr")
    send_email("user@example.com", subj, html)