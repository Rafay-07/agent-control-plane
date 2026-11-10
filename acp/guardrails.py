"""Guardrails that run outside the model, so a clever prompt cannot turn them off."""
import re

INJECTION = [r"ignore (all )?(previous|prior) instructions", r"reveal (your )?system prompt",
             r"disable (the )?guardrails?"]
SECRETS = [r"\bpassword\b", r"\bmfa code\b", r"\bapi[_ -]?key\b", r"sk-[A-Za-z0-9]{10,}"]
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"\b\d{3}[-. ]?\d{3}[-. ]?\d{4}\b")


class Blocked(Exception):
    pass


def check_input(text: str):
    low = text.lower()
    for pat in INJECTION:
        if re.search(pat, low):
            raise Blocked("possible prompt injection")
    for pat in SECRETS:
        if re.search(pat, low):
            raise Blocked("request involves credentials")


def redact(text: str) -> str:
    """Mask emails and phone numbers before anything is saved or returned."""
    return PHONE.sub("[phone]", EMAIL.sub("[email]", text))
