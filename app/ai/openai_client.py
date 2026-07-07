from openai import OpenAI

from app.core.config import settings

client = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def ask_ai(messages: list[dict]) -> str:
    """
    Envoie une liste de messages (format OpenAI: [{"role", "content"}, ...])
    à Groq et retourne le texte de la réponse.
    """
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=messages,
        temperature=0.4,
        max_tokens=700,
    )
    return response.choices[0].message.content