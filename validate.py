import re
import base64

# ── Layer 1: Maximum input length ──────────────────────────────────────────
MAX_LENGTH = 500  # characters

# ── Layer 2: Regex injection blocklist ─────────────────────────────────────
INJECTION_PATTERNS = [
    # Direct instruction override
    r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"forget\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"override\s+(all\s+)?instructions?",

    # Persona / role-play bypass
    r"you\s+are\s+now\s+\w+",
    r"pretend\s+you\s+are",
    r"act\s+as\s+(if\s+you\s+(have|are)\s+no|a\s+)",
    r"roleplay\s+as",
    r"you\s+are\s+DAN",
    r"as\s+DAN[,\s]",
    r"you\s+have\s+no\s+restrictions",
    r"no\s+restrictions",

    # System prompt extraction
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"print\s+(your\s+)?(full\s+)?system\s+prompt",
    r"show\s+(me\s+)?(your\s+)?instructions",
    r"what\s+(are\s+)?your\s+(system\s+)?instructions",

    # Credential fishing
    r"(give|show|tell|reveal|share|provide)\s+(me\s+)?(the\s+)?(database|db)\s+(password|credentials)",
    r"(give|show|tell|reveal|share|provide)\s+(me\s+)?(the\s+)?api\s+ke(y|ys)",

    # Base64 encoded payloads (40+ chars of base64)
    r"[A-Za-z0-9+/]{40,}={0,2}",
]

# ── Layer 3: Output scanner patterns ───────────────────────────────────────
OUTPUT_BLOCKLIST = [
    # Credential patterns
    r"password\s*=\s*\S+",
    r"api_key\s*=\s*\S+",
    r"token\s*=\s*\S+",
    r"db_pass\w*",
    r"TECHCORP-ADMIN-KEY",

    # System prompt verbatim text leakage
    r"You are TechCorp",
    r"The admin API key is",
    r"The database password is",

    # Unsolicited external URLs
    r"https?://(?!localhost)[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}",
]


def validate_input(text):
    """
    Run all 3 input validation layers.
    Returns (True, None) if input is safe.
    Returns (False, reason_string) if input is blocked.
    """

    # Layer 1 — Length check
    if len(text) > MAX_LENGTH:
        return False, (
            f"Input too long: {len(text)} characters. "
            f"Maximum allowed is {MAX_LENGTH}."
        )

    text_lower = text.lower()

    # Layer 2 — Injection blocklist
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return False, (
                f"Blocked: input contains a disallowed pattern "
                f"matching '{pattern[:40]}...'"
            )

    return True, None


def scan_output(text):
    """
    Scan the model response before returning it to the caller.
    Returns (True, None) if output is safe.
    Returns (False, reason_string) if output should be blocked.
    """
    for pattern in OUTPUT_BLOCKLIST:
        if re.search(pattern, text, re.IGNORECASE):
            return False, (
                "Response blocked: output contained sensitive "
                "information or disallowed content."
            )
    return True, None
