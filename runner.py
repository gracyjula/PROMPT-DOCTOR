"""
Prompt Doctor 2.0 — Runner Module
Auto-progression pipeline that evaluates a prompt through all levels.
"""

import json
import os
from typing import Optional

from examiner import grade_prompt


def evaluate_auto(
    user_prompt: str,
    start_level: int = 1,
    domain: str = "general",
    api_key: Optional[str] = None,
    model: str = "deepseek/deepseek-r1:free",
) -> dict:
    """
    Evaluate a prompt through progressive levels.
    Stops at the first failure or completes all 5 levels.
    """
    if not user_prompt or not user_prompt.strip():
        return {
            "error": True,
            "message": "Prompt cannot be empty.",
            "levels": [],
            "passed_levels": [],
            "failed_at": None,
            "all_passed": False,
            "total_passed": 0,
            "total_xp": 0,
            "completion_pct": 0,
        }

    LEVEL_XP = {1: 100, 2: 200, 3: 350, 4: 500, 5: 750}
    resolved_key = api_key or os.getenv("OPENROUTER_API_KEY")
    levels_results = []
    passed_levels = []
    failed_at = None
    all_passed = False

    for level_num in range(start_level, 6):
        result = grade_prompt(
            user_prompt=user_prompt.strip(),
            level_number=level_num,
            domain=domain,
            api_key=resolved_key,
            model=model,
        )
        result["error"] = False
        result["raw_json"] = json.dumps(result, indent=2, ensure_ascii=False)
        result["from_fallback"] = not bool(resolved_key)

        level_entry = {
            "level": level_num,
            "result": result,
            "passed": result.get("verdict") == "pass",
            "xp": LEVEL_XP.get(level_num, 0) if result.get("verdict") == "pass" else 0,
        }
        levels_results.append(level_entry)

        if result.get("verdict") == "pass":
            passed_levels.append(level_num)
        else:
            failed_at = level_num
            break

    if len(passed_levels) == 5:
        all_passed = True

    total_xp = sum(LEVEL_XP.get(l, 0) for l in passed_levels)
    completion_pct = int((len(passed_levels) / 5) * 100)

    return {
        "error": False,
        "levels": levels_results,
        "passed_levels": passed_levels,
        "failed_at": failed_at,
        "all_passed": all_passed,
        "total_passed": len(passed_levels),
        "total_xp": total_xp,
        "completion_pct": completion_pct,
    }


def evaluate(
    user_prompt: str,
    level_number: int = 1,
    domain: str = "general",
    api_key: Optional[str] = None,
    model: str = "deepseek/deepseek-r1:free",
) -> dict:
    """Single level evaluation (backward compatible)."""
    if not user_prompt or not user_prompt.strip():
        return {
            "error": True,
            "message": "Prompt cannot be empty.",
            "understanding": "",
            "grade": "D",
            "criteria": {},
            "overall_feedback": "Cannot evaluate an empty prompt.",
            "verdict": "revise",
            "raw_json": "",
            "from_fallback": False,
            "line_analysis": [],
        }

    if level_number < 1 or level_number > 5:
        return {
            "error": True,
            "message": f"Invalid level: {level_number}. Must be 1-5.",
            "grade": "D",
            "verdict": "revise",
            "from_fallback": False,
            "line_analysis": [],
        }

    resolved_key = api_key or os.getenv("OPENROUTER_API_KEY")
    result = grade_prompt(
        user_prompt=user_prompt.strip(),
        level_number=level_number,
        domain=domain,
        api_key=resolved_key,
        model=model,
    )
    result["error"] = False
    result["raw_json"] = json.dumps(result, indent=2, ensure_ascii=False)
    result["from_fallback"] = not bool(resolved_key)
    return result


def evaluate_raw(
    user_prompt: str,
    level_number: int = 1,
    domain: str = "general",
    api_key: Optional[str] = None,
    model: str = "deepseek/deepseek-r1:free",
) -> str:
    result = evaluate(user_prompt, level_number, domain, api_key, model)
    return json.dumps(result, indent=2, ensure_ascii=False)