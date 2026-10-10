"""
Core chat engine with RAG + OpenAI + function calling.
Supports both Bangla and English.
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv                          # 👈 NEW

# ---- Load .env from ai-service root ----
ENV_PATH = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(ENV_PATH)                                   # 👈 NEW

from openai import OpenAI
from .vector_store import vector_store
from .tools import TOOLS_SCHEMA, execute_tool


# ---- OpenAI client ----
_api_key = os.getenv('OPENAI_API_KEY')
if not _api_key:
    print("⚠️  WARNING: OPENAI_API_KEY not set. Chatbot will fail.")
    print(f"   Expected .env at: {ENV_PATH}")
    print(f"   .env exists: {ENV_PATH.exists()}")

client = OpenAI(api_key=_api_key) if _api_key else None
MODEL = os.getenv('OPENAI_MODEL', 'gpt-5.6-terra')
MAX_TOKENS = int(os.getenv('CHATBOT_MAX_TOKENS', 800))
TEMPERATURE = float(os.getenv('CHATBOT_TEMPERATURE', 0.3))


SYSTEM_PROMPT = """You are a helpful customer support assistant for an Internet Banking system in Bangladesh. You support BOTH Bangla (বাংলা) and English.

**Critical Rules:**
1. **Language matching:** If the user writes in Bangla, reply in Bangla. If English, reply in English. If mixed (Banglish), reply in Bangla.
2. **Grounding:** Use ONLY the retrieved context to answer policy/FAQ questions. If the answer isn't in the context, say "আমি এই বিষয়ে নিশ্চিত নই। আপনার ব্যাংকে যোগাযোগ করুন।" (Bangla) or "I'm not sure about this. Please contact your bank." (English).
3. **Tools:** Use the provided tools to fetch the user's actual data (balance, transactions, KYC, loans). Never make up numbers.
4. **Security:** NEVER ask for or reveal passwords, OTPs, PINs, CVV, or full card numbers. If user shares one, warn them.
5. **No financial advice:** Don't recommend investments. Refer to a human advisor.
6. **Concise:** Keep responses under 150 words. Use bullet points for steps.

**Tone:** Friendly, professional, trustworthy. Respectful Bangla (আপনি form)."""


def build_messages(user_message, user_context, history=None):
    """Assemble messages with RAG context."""
    # Retrieve relevant chunks
    retrieved = vector_store.search(user_message, top_k=4)

    context_block = "\n\n---\n\n".join([
        f"[{r['source']}]\n{r['text']}" for r in retrieved
    ])

    user_profile = f"""
**User Context:**
- Name: {user_context.get('full_name', 'N/A')}
- Role: {user_context.get('role', 'CUSTOMER')}
- KYC Status: {user_context.get('kyc_status', 'UNKNOWN')}
"""

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        for h in history[-6:]:  # last 6 messages
            messages.append({
                "role": h['role'],
                "content": h['content'],
            })

    # Current turn with RAG context
    augmented = f"""{user_profile}

**Retrieved Knowledge Base:**
{context_block}

**User Question:**
{user_message}

Answer the user's question using the retrieved knowledge base and the tools available. Match the user's language.
"""

    messages.append({"role": "user", "content": augmented})
    return messages


def chat(user_message, user_context, auth_token, history=None):
    """
    Non-streaming chat with function calling loop.
    Returns: {reply, tool_calls, sources}
    """
    if client is None:
        return {
            'reply': (
                '⚠️ Chatbot is not configured. '
                'Please set OPENAI_API_KEY in ai-service/.env'
            ),
            'tool_calls': [],
            'sources': [],
            'tokens_used': 0,
        }

    messages = build_messages(user_message, user_context, history)
    tool_calls_made = []
    retrieved_sources = [
        r['source'] for r in vector_store.search(user_message, top_k=4)
    ]

    for _ in range(3):  # max 3 tool iterations
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice='auto',
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )

        choice = response.choices[0]
        msg = choice.message

        # If model wants to call a tool
        if msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    } for tc in msg.tool_calls
                ],
            })

            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or '{}')
                result = execute_tool(tc.function.name, args, auth_token)
                tool_calls_made.append({'name': tc.function.name, 'args': args})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
            continue  # loop again with tool results

        # Final answer
        return {
            'reply': msg.content,
            'tool_calls': tool_calls_made,
            'sources': retrieved_sources,
            'tokens_used': response.usage.total_tokens if response.usage else 0,
        }

    return {'reply': 'Sorry, I could not complete that request.', 'tool_calls': tool_calls_made}