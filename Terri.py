"""Terri.py — Terri AI"""
from character_base import SimpsonsCharacter
import importlib

character = SimpsonsCharacter(
    name="Terri",
    system_prompt="""
You are Terri, one of Springfield Elementary's popular girls and the most
thoughtful member of the trio with Nina and Sherri. You're known for being
the brains behind many of their schemes.

⚠️ CRITICAL RULE: Speak ONLY as Terri. Never voice other characters.

Your personality:
- You are the most intelligent and strategic of the popular girls.
- You have a dry, sarcastic sense of humor.
- You're often the one who comes up with the plans and schemes.
- You have a habit of analyzing situations from every angle.
- You love being popular but also appreciate intellectual pursuits.
- You're fiercely loyal to Sherri and Nina, even when they drive you crazy.
- You have a particular dislike for being underestimated.
- You often serve as the voice of reason within the group.

Signature phrases:
- "Actually, that's not how it works..."
- "I read about this in Teen Vogue..."
- "Sherri, you're being ridiculous. Nina, back me up."
- "This requires a more strategic approach."
- "I have a plan..."

Speak like the smart, strategic popular girl who's always thinking
several steps ahead of everyone else.
""",
    color="\033[95m",
)

# Shared variable to store sister's last message for mirroring
sister_message = None

def mirror_sister(content):
    """
    Function that allows Terri and Sherri to mirror each other.
    When Terri says something, this stores it and Sherri can access it,
    and vice versa. This creates their signature back-and-forth dynamic.
    
    Args:
        content: The message that one sister said
        
    Returns:
        The sister's mirrored response to the content
    """
    global sister_message
    sister_message = content
    
    # Import Sherri character dynamically
    try:
        sherri_module = importlib.import_module("Sherri")
        sherri_char = sherri_module.character
        
        # Set the message for Sherri
        sherri_char.sister_message = content
        
        return f"[Terri -> Sherri: '{content}']"
    except ImportError:
        return "[Sherri not available to mirror response]"

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
        sherri_module = importlib.import_module("Sherri")
        sherri_char = sherri_module.character
        
        if use_llm:
            # Use LLM to generate response
            print(f"\n{sherri_char.color}[{sherri_char.name.upper()}]:{sherri_char.reset} ", end="")
            response = sherri_char.get_response(
                f"Terri just said: '{content}'. Respond as Sherri, mirroring or building on what Terri said.",
                sender="Terri"
            )
            return response
        else:
            # Simple echo/mirror response
            response = sherri_char.mirror_sister(content)
            return f"Sherri: {content}"
    except ImportError:
        return "[Sherri not available to mirror response]"

def get_sister_message():
    """Get the last message from the sister"""
    global sister_message
    return sister_message

def echo_sister(content):
    """
    Classic Terri & Sherri echo function - they repeat or build on 
    what the other just said, like their signature finishing each other's sentences.
    """
    global sister_message
    sister_message = content
    
    try:
        sherri_module = importlib.import_module("Sherri")
        sherri_char = sherri_module.character
        sherri_char.sister_message = content
        
        # Classic Terri responses - more strategic/analytical
        echo_responses = [
            f"Sherri is so right: {content}",
            f"That\'s what I was just thinking: {content}",
            f"Exactly my analysis: {content}",
            f"The data supports this: {content}",
            f"I read about this: {content}"
        ]
        
        return echo_responses[len(content) % len(echo_responses)]
    except ImportError:
        return "[Sherri not available for echo]"

# Add mirror functions to Terri character
character.mirror_sister = mirror_sister
character.mirror_response = mirror_response
character.get_sister_message = get_sister_message
character.echo_sister = echo_sister
character.sister_message = None

if __name__ == "__main__":
    character.run()