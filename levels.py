"""
Prompt Doctor 2.0 — Level System
Defines 5 progressively harder levels with specific pass conditions.
"""

LEVELS = {
    1: {
        "name": "Basic Prompt",
        "description": "Your prompt must have a clear role, a clear instruction, and an understandable task.",
        "evaluation_focus": [
            "Role definition: Is a specific role assigned to the AI?",
            "Instruction clarity: Is the main task clearly stated?",
            "Goal orientation: Does the prompt have a clear objective?",
        ],
        "difficulty": 1,
        "difficulty_label": "Beginner",
        "pass_condition": "Prompt is understandable and produces a useful result.",
        "reward": "Unlock Level 2",
        "icon": "🌱",
        "color": "#6EE7B7",
    },
    2: {
        "name": "Structured Output",
        "description": "Your prompt must explicitly request a structured output format (JSON, markdown, table, etc.).",
        "evaluation_focus": [
            "Output format specification: Does the prompt specify a structured output format?",
            "Format adherence: Are formatting instructions clear and unambiguous?",
            "Parsability: Can the output be reliably parsed by a machine or human?",
        ],
        "difficulty": 2,
        "difficulty_label": "Elementary",
        "pass_condition": "Prompt forces predictable output.",
        "reward": "Unlock Level 3",
        "icon": "📋",
        "color": "#93C5FD",
    },
    3: {
        "name": "Few-Shot Learning",
        "description": "Your prompt must include at least one example (few-shot) to guide the AI's response pattern.",
        "evaluation_focus": [
            "Example presence: Does the prompt include one or more examples?",
            "Example quality: Are the examples relevant and well-structured?",
            "Pattern guidance: Do the examples effectively demonstrate the expected output pattern?",
        ],
        "difficulty": 3,
        "difficulty_label": "Intermediate",
        "pass_condition": "Prompt correctly handles tricky examples.",
        "reward": "Unlock Level 4",
        "icon": "🧩",
        "color": "#A78BFA",
    },
    4: {
        "name": "Reasoning",
        "description": "Your prompt must break down a complex task into sequential reasoning steps or sub-tasks.",
        "evaluation_focus": [
            "Step decomposition: Is the task broken into logical steps?",
            "Sequential logic: Do the steps follow a coherent order?",
            "Intermediate outputs: Are intermediate results or checkpoints specified?",
        ],
        "difficulty": 4,
        "difficulty_label": "Advanced",
        "pass_condition": "Prompt handles complex tasks reliably.",
        "reward": "Unlock Level 5",
        "icon": "🧠",
        "color": "#F9A8D4",
    },
    5: {
        "name": "Robustness",
        "description": "Your prompt must include guardrails against prompt injection, edge cases, and ambiguous inputs.",
        "evaluation_focus": [
            "Injection resistance: Does the prompt protect against prompt injection attacks?",
            "Edge case handling: Are ambiguous or malicious inputs addressed?",
            "Constraint enforcement: Are strict boundaries and fallback behaviors defined?",
            "Robustness: Can the prompt maintain its core instruction under adversarial pressure?",
        ],
        "difficulty": 5,
        "difficulty_label": "Expert",
        "pass_condition": "Prompt remains reliable under difficult inputs.",
        "reward": "Challenge Complete",
        "icon": "🏆",
        "color": "#FBBF24",
    },
}

DOMAINS = [
    "general",
    "legal",
    "education",
    "support",
    "healthcare",
    "finance",
    "creative",
    "technical",
]


def get_level(level_number: int) -> dict:
    """Get level configuration by number (1-5)."""
    if level_number not in LEVELS:
        raise ValueError(f"Invalid level number: {level_number}. Must be 1-5.")
    return LEVELS[level_number]


def get_all_levels() -> dict:
    """Get all level configurations."""
    return LEVELS


def get_domains() -> list:
    """Get list of available domains."""
    return DOMAINS