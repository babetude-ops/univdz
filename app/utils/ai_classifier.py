import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

URL = "https://api.groq.com/openai/v1/chat/completions"


def classify_event(text):

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
Classifie cette annonce académique.

Répond seulement par un mot parmi :

colloque
séminaire
appel
bourse

Texte :
{text}
"""

    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }

    try:

        r = requests.post(URL, headers=headers, json=data, timeout=20)

        result = r.json()

        if "choices" in result:
            response = result["choices"][0]["message"]["content"].lower()

            if "colloque" in response:
                return "colloque"

            if "séminaire" in response or "seminaire" in response:
                return "séminaire"

            if "bourse" in response:
                return "bourse"

            if "appel" in response:
                return "appel"

    except Exception as e:
        print("Groq erreur :", e)

    # classification de secours (sans IA)

    text = text.lower()

    if "bourse" in text or "scholarship" in text:
        return "bourse"

    if "colloque" in text or "conference" in text:
        return "colloque"

    if "séminaire" in text or "seminaire" in text:
        return "séminaire"

    if "appel" in text:
        return "appel"

    # dernier fallback
    return "appel"