from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

def generate_ideas(topic, language, count=20):

    prompt = f"""
Generate {count} ebook ideas about "{topic}".

Language: {language}

Requirements:
- clear and marketable titles
- no numbering
- no extra explanation

IMPORTANT:
- If Korean → write in Korean
- If English → write in English
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text