import os
from openai import OpenAI
import textwrap

OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')  # change if you prefer another

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def summarize_with_openai(query: str, sources: list) -> str:
    # Build the prompt/messages
    system = ("You are an assistant that reads the provided source texts and writes a short structured report:"
              " include a 3-6 bullet key-takeaways, a short summary paragraph, and per-source short notes (1-2 lines).")

    user_parts = [f"Query: {query}\n\n"]
    for s in sources:
        snippet = s.get('text', '')[:4000]  # truncate very long content to keep token usage reasonable
        user_parts.append(f"---\nURL: {s.get('url')}\nTitle: {s.get('title')}\nText:\n{snippet}\n\n")
    user_message = "\n".join(user_parts)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_message}
        ],
        max_tokens=800,
        temperature=0.2
    )

    # response payload structure : choices[0].message.content
    content = response.choices[0].message.content
    return content.strip()
