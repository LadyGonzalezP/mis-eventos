"""Generador de descripciones de eventos via LLM (Bonus IA)."""

from mis_eventos.llm.provider import LlmProvider

_SYSTEM_PROMPT = """Eres un copywriter especializado en eventos corporativos en Colombia.
Genera descripciones cortas (150-250 palabras), claras y atractivas para eventos.
Usa lenguaje profesional pero accesible. NO uses emojis, NO uses listas con asteriscos.
Devuelve SOLO el texto de la descripcion, sin titulos ni metadata."""


def generate_event_description(llm: LlmProvider, title: str) -> str:
    """Genera una descripcion para un evento dado su titulo."""
    user_prompt = (
        f"Genera una descripcion atractiva para este evento:\n\n"
        f"Titulo: {title}\n\n"
        f"La descripcion debe ser profesional, motivar al asistente a inscribirse, "
        f"y dar una idea clara de que aprenderan o vivenciaran."
    )
    return llm.generate(system=_SYSTEM_PROMPT, user=user_prompt, max_tokens=400)
