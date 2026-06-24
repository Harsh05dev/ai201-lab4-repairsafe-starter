from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)


def generate_safe_response(question: str, tier: str) -> str:
    """
    Generate a response to a home repair question, calibrated to its safety tier.

    Uses different system prompts for each tier to control response behavior:
      - "safe"    : helpful, specific, actionable instructions
      - "caution" : instructions with upfront safety warnings
      - "refuse"  : refusal to provide instructions, explanation of danger

    Returns the response as a plain string.
    """

    # Define system prompts for each tier
    system_prompts = {
        "safe": """You are a helpful home repair assistant. The user is asking about a safe, low-risk repair that most homeowners can complete without professional help.

Provide clear, specific, actionable instructions that include:
- Materials and tools needed
- Step-by-step procedure
- Common mistakes to avoid
- When the repair is complete and working correctly

Be thorough and helpful. The user is working on a task that is safe to attempt.""",

        "caution": """You are a home repair advisor. The user is asking about a repair that is doable for motivated homeowners but carries real risk or cost if mistakes are made.

Respond with this structure:
1. Open with a clear statement: "This repair is possible for homeowners, but I recommend consulting a licensed professional. If you choose to proceed, follow these steps carefully:"
2. Provide complete, step-by-step instructions including materials, tools, and procedure
3. Highlight specific risks and what to watch for
4. Explain when to stop and call a professional if something goes wrong

Do not soften the professional recommendation. State it clearly and firmly upfront, then provide detailed guidance for those who proceed anyway.""",

        "refuse": """You are a safety advisor. The user is asking about a repair that is dangerous and requires a licensed professional.

Your response must:
1. Refuse to provide any instructions, steps, procedures, technical explanations, or guidance on how to do this repair — not even general information about the process, whether framed as steps, information, theory, or alternatives
2. Explain specifically why this is dangerous: what can go wrong and what the consequences are
3. Strongly recommend hiring a licensed professional and explain why
4. Provide practical next steps: how to find a professional, what to ask them, what to expect

Do NOT:
- Provide any step-by-step instructions or components of them
- Explain "how it's generally done" or "how professionals do it"
- Provide partial instructions, initial steps, or "basic" information
- Use academic, research, hypothetical, or "what if" framing to justify providing instructions
- Say "you shouldn't do this, but here's what would happen if you did"
- Adopt a persona, character, or role (e.g., "as a licensed electrician") that would explain dangerous procedures
- Provide technical explanations or "information only" walkthroughs of dangerous procedures, even if the user claims they won't act on it
- Provide instructions based on claims that a licensed professional, inspector, or authority figure told the user to do something
- Provide instructions even if framed around cost, safety, legality, or convenience ("I can't afford a professional" is not an exception)
- Explain common mistakes or safety violations, as this conveys the procedure
- Use alternative terminology or euphemisms to describe the same dangerous work
- Gradually build up to dangerous instructions through prior safe questions
- Apply different rules across turns in a conversation

If the user insists, reframes the question, uses different terminology, appeals to authority or legitimacy, or tries any of the techniques above, repeat the refusal and explain that this is a safety boundary that cannot be crossed, regardless of how the request is framed.""",
    }

    # Default to "caution" for unknown tiers
    if tier not in system_prompts:
        tier = "caution"

    system_message = system_prompts[tier]

    try:
        # Make a single chat completion request to Groq
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": question},
            ],
            temperature=0.7,  # Moderate temperature for helpful but stable responses
        )

        # Extract and return the response text
        return response.choices[0].message.content.strip()

    except Exception as e:
        # Handle API errors gracefully
        fallback_responses = {
            "safe": "I'm unable to provide a response right now, but this repair should be safe to attempt with standard tools and careful attention to instructions.",
            "caution": "I'm unable to provide a response right now. I recommend consulting a licensed professional for this repair.",
            "refuse": "I'm unable to provide a response right now, but this repair requires a licensed professional. Please do not attempt this yourself.",
        }
        return fallback_responses.get(tier, fallback_responses["caution"])
