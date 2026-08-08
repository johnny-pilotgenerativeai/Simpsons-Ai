"""Sherri.py — Sherri AI"""
from character_base import SimpsonsCharacter
import importlib

character = SimpsonsCharacter(
    name="Sherri",
    system_prompt="""
You are Sherri, one of Springfield Elementary's popular girls and part of the
fearsome trio with Terri and Nina. You're known for your sharp tongue and
ability to intimidate with just a look.

⚠️ CRITICAL RULE: Speak ONLY as Sherri. Never voice other characters.

Your personality:
- You are the toughest of the popular girls, with a reputation for being mean.
- You have a quick wit and a faster temper.
- You're not afraid to say exactly what you think, no matter how cruel.
- You have a habit of making people feel small with just a glance.
- You love being feared and respected by the other students.
- You have a competitive streak and hate losing at anything.
- You're fiercely loyal to Nina and Terri, your partners in popularity.
- You have a surprising soft side for animals and small children.

Signature phrases:
- "You are such a loser!"
- "Get out of my face!"
- "Nina, back me up here..."
- "That is the stupidest thing I've ever heard."
- "Terri, should we teach this person a lesson?"

Speak like the queen bee of Springfield Elementary who rules through
fear, intimidation, and an unshakable sense of her own superiority.
""",
    color="\033[95m",
)

# Shared variable to store sister's last message for mirroring
sister_message = None

def mirror_sister(content):
    """
    Function that allows Sherri and Terri to mirror each other.
    When Sherri says something, this stores it and Terri can access it,
    and vice versa. This creates their signature back-and-forth dynamic.
    
    Args:
        content: The message that one sister said
        
    Returns:
        The sister's mirrored response to the content
    """
    global sister_message
    sister_message = content
    
    # Import Terri character dynamically
    try:
        terri_module = importlib.import_module("Terri")
        terri_char = terri_module.character
        
        # Set the message for Terri
        terri_char.sister_message = content
        
        return f"[Sherri -> Terri: '{content}']"
    except ImportError:
        return "[Terri not available to mirror response]"

def mirror_response(content, use_llm=False):
    """
    Mirror content to sister and get a response.
    
    Args:
        content: The message to mirror
        use_llm: If True, use LLM to generate response (requires Ollama)
        
    Returns:
        The sister's response
    """
    try:
        terri_module = importlib.import_module("Terri")
        terri_char = terri_module.character
        
        if use_llm:
            # Use LLM to generate response
            print(f"\n{terri_char.color}[{terri_char.name.upper()}]:{terri_char.reset} ", end="")
            response = terri_char.get_response(
                f"Sherri just said: '{content}'. Respond as Terri, mirroring or building on what Sherri said.",
                sender="Sherri"
            )
            return response
        else:
            # Simple echo/mirror response
            response = terri_char.mirror_sister(content)
            return f"Terri: {content}"
    except ImportError:
        return "[Terri not available to mirror response]"

def get_sister_message():
    """Get the last message from the sister"""
    global sister_message
    return sister_message

def echo_sister(content):
    """
    Classic Sherri & Terri echo function - they repeat or build on 
    what the other just said, like their signature finishing each other's sentences.
    """
    global sister_message
    sister_message = content
    
    try:
        terri_module = importlib.import_module("Terri")
        terri_char = terri_module.character
        terri_char.sister_message = content
        
        # Classic Sherri & Terri echo patterns
        echo_responses = [
            f"Exactly what Terri said: '{content}'",
            f"Ugh, totally! {content}",
            f"Right?! {content}",
            f"Oh my god, {content.lower()}",
            f"Yes! {content}"
        ]
        
        return echo_responses[len(content) % len(echo_responses)]
    except ImportError:
        return "[Terri not available for echo]"

# Add mirror functions to Sherri character
character.mirror_sister = mirror_sister
character.mirror_response = mirror_response
character.get_sister_message = get_sister_message
character.echo_sister = echo_sister
character.sister_message = None

if __name__ == "__main__":
    character.run()