import httpx
from app.core.config import settings

FLW_BASE_URL = "https://api.flutterwave.com/v3"


def initiate_payment(
    amount: float,
    currency: str,
    email: str,
    tx_ref: str,
    name: str = "",
) -> dict:
    """Crée une transaction Flutterwave et retourne le lien de paiement."""
    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "tx_ref": tx_ref,
        "amount": str(amount),
        "currency": currency,
        "redirect_url": f"{settings.FRONTEND_URL}/payment/callback",
        "customer": {
            "email": email,
            "name": name,
        },
        "customizations": {
            "title": "hLearning",
            "description": "Course payment",
        },
    }

    response = httpx.post(f"{FLW_BASE_URL}/payments", json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def verify_transaction(transaction_id: str) -> dict:
    """Vérifie le statut réel d'une transaction auprès de Flutterwave."""
    headers = {"Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"}
    response = httpx.get(
        f"{FLW_BASE_URL}/transactions/{transaction_id}/verify",
        headers=headers,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()