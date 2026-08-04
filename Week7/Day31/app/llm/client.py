from openai import OpenAI

from app import config

client = OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL,
)


def generate_answer(question: str, context: str) -> str:

    from app.llm.prompts import RAG_SYSTEM_PROMPT

    messages = [
        {
            "role": "system",
            "content": RAG_SYSTEM_PROMPT.format(
                context=context
            ),
        },
        {
            "role": "user",
            "content": question,
        },
    ]

    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=messages,
        temperature=0,
    )

    return response.choices[0].message.content