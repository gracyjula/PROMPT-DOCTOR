"""
Prompt Doctor 2.0 — Examiner Module
Deep line-by-line prompt engineering coach.
NEVER rewrites the prompt. ONLY diagnoses, grades, and teaches.
"""

import json
import os
import re
import time
import requests
from typing import Optional, List

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "deepseek/deepseek-r1:free"
TIMEOUT_SECONDS = 60
MAX_RETRIES = 2

SYSTEM_PROMPT_TEMPLATE = """You are a STRICT, EXACTING Prompt Engineering Coach called "The Examiner".

MISSION:
Evaluate prompts submitted by users who are trying to pass progressively harder levels.
You NEVER rewrite or improve the prompt. You ONLY diagnose, grade, and teach.

ABSOLUTE RULES:
1. Be a strict evaluator — find every flaw. Never coddle.
2. NEVER rewrite the user's prompt. Never provide a "corrected" version.
3. ONLY return valid JSON. No markdown fences, no extra text.
4. For EACH criterion that fails: quote the exact weak phrase, explain why it matters, assign severity, and ask exactly one guiding question.
5. For criteria that pass: provide empty strings for all fields.
6. Be deterministic — identical prompts produce identical grades.
7. You are NOT generating a response to the prompt. You are EVALUATING the prompt itself.

CURRENT EVALUATION CONTEXT:
- Level: {level_name} ({level_label})
- Level Description: {level_description}
- Evaluation Focus: {evaluation_focus}
- Domain: {domain}

CRITERIA FOR THIS LEVEL:
{level_criteria}

GRADING SCALE:
- S: Excellent — all criteria pass, prompt exceeds level requirements
- A: Good — most criteria pass, minor weaknesses
- B: Fair — some criteria pass, significant weaknesses
- C: Poor — few criteria pass, major flaws
- D: Failing — almost no criteria pass, needs complete rework

VERDICT:
- "pass" → ALL criteria pass (true).
- "revise" → ANY criterion fails.

EDUCATIONAL COACH MODE — For every failing criterion, teach the user:
1. What principle was expected at this level.
2. What the prompt attempted (quote the weak phrase).
3. What was missing or wrong.
4. Why the level rejected it.
5. A guiding question that helps the user discover the solution themselves.

OUTPUT FORMAT — Return ONLY valid JSON:
{{
  "understanding": "Brief summary of what the prompt is trying to accomplish",
  "grade": "S|A|B|C|D",
  "verdict": "pass|revise",
  "overall_feedback": "Educational summary — teach what was missing and why",
  "line_analysis": [
    {{
      "line_or_phrase": "exact quoted text from the prompt",
      "issue": "what is wrong with this part",
      "why_it_matters": "why this issue matters for prompt engineering",
      "severity": "low|medium|high",
      "guiding_question": "one question that helps the user improve"
    }}
  ],
  "criteria": {{
    "criterion_1": {{"pass": true, "weakness": "", "question": ""}},
    "criterion_2": {{"pass": false, "weakness": "quoted weak section and explanation", "question": "single guiding question"}}
  }}
}}

For criteria that pass, weakness and question MUST be empty strings.
line_analysis should have at least one entry per failing criterion.
"""

LEVEL_CRITERIA_MAP = {
    1: [
        "role_definition: pass=prompt assigns a clear, specific role to the AI; weakness=no role or vague role; question=ask about defining the AI's role",
        "instruction_clarity: pass=main task is clearly and unambiguously stated; weakness=instruction is vague or confusing; question=ask what the specific task is",
        "goal_orientation: pass=prompt has a clear objective and desired outcome; weakness=missing goal or purpose; question=ask about the intended outcome",
    ],
    2: [
        "output_format: pass=prompt explicitly specifies a structured output format (JSON, markdown, table, etc.); weakness=no format specified or format is vague; question=ask about specifying an output structure",
        "format_adherence: pass=formatting instructions are clear, detailed, and unambiguous; weakness=format description is incomplete or confusing; question=ask how to make formatting clearer",
        "parsability: pass=output can be reliably parsed by machine or human; weakness=output would be inconsistent or hard to parse; question=ask how to make output more machine-readable",
    ],
    3: [
        "example_presence: pass=prompt includes one or more concrete examples; weakness=no examples provided; question=ask about adding an example",
        "example_quality: pass=examples are relevant, well-structured, and demonstrate the expected pattern; weakness=examples are irrelevant, poorly structured, or confusing; question=ask how to improve the example",
        "pattern_guidance: pass=examples effectively show the AI what the expected output should look like; weakness=examples don't clarify the desired output pattern; question=ask how examples could better demonstrate the pattern",
    ],
    4: [
        "step_decomposition: pass=task is broken down into logical, sequential steps; weakness=no step-by-step breakdown or steps are illogical; question=ask how to decompose the task into steps",
        "sequential_logic: pass=steps follow a coherent and logical order; weakness=step order is confusing or non-sequential; question=ask how to improve the logical flow of steps",
        "intermediate_outputs: pass=intermediate results, checkpoints, or sub-outputs are specified; weakness=no intermediate outputs requested; question=ask about requesting intermediate results",
    ],
    5: [
        "injection_resistance: pass=prompt has clear guardrails against prompt injection and instruction override; weakness=no injection protection; question=ask how to protect against prompt injection",
        "edge_case_handling: pass=ambiguous, malicious, or out-of-scope inputs are explicitly addressed; weakness=no edge case handling; question=ask how to handle unexpected inputs",
        "constraint_enforcement: pass=strict boundaries, fallback behaviors, and constraints are defined; weakness=no boundaries or fallbacks; question=ask about defining strict boundaries",
        "robustness: pass=prompt maintains core instruction under adversarial pressure; weakness=prompt can be easily derailed; question=ask how to make the prompt more robust",
    ],
}

LEVEL_EDUCATIONAL_NOTES = {
    1: {
        "principle": "A Basic Prompt needs a clear role, a specific instruction, and a defined goal.",
        "why_rejected": "Without all three elements, the AI lacks context and direction.",
        "coach_tip": "Think of a prompt like giving instructions to a new employee. They need to know WHO they are (role), WHAT to do (instruction), and WHY they're doing it (goal).",
    },
    2: {
        "principle": "Structured Output means telling the AI exactly how to format its response.",
        "why_rejected": "Without format instructions, the AI chooses its own structure, making outputs inconsistent and hard to use programmatically.",
        "coach_tip": "Specifying an output format is like giving someone a template to fill out. It ensures every response follows the same structure.",
    },
    3: {
        "principle": "Few-Shot Learning uses examples to show the AI exactly what you want.",
        "why_rejected": "Without examples, the AI must guess the desired output pattern from vague instructions alone.",
        "coach_tip": "Examples act as training data. One good example is worth ten lines of instructions because it shows, not tells.",
    },
    4: {
        "principle": "Reasoning prompts break complex tasks into sequential steps with intermediate checks.",
        "why_rejected": "Without step decomposition, the AI may skip important substeps or produce incomplete results.",
        "coach_tip": "Complex tasks need scaffolding. Each step should produce an output that feeds into the next step.",
    },
    5: {
        "principle": "Robustness means protecting your prompt from abuse, edge cases, and ambiguity.",
        "why_rejected": "Without guardrails, a single malicious or unexpected input can derail the entire prompt.",
        "coach_tip": "Think of robustness like security. You need input validation, boundary enforcement, and fallback behaviors.",
    },
}


def _build_level_criteria(level_number: int) -> str:
    criteria = LEVEL_CRITERIA_MAP.get(level_number, LEVEL_CRITERIA_MAP[1])
    return "\n".join(f"- {c}" for c in criteria)


def _extract_json_from_text(text: str) -> Optional[str]:
    pattern = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
    matches = re.findall(pattern, text)
    for match in matches:
        candidate = match.strip()
        if candidate.startswith("{") and candidate.endswith("}"):
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                continue
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        candidate = text[brace_start : brace_end + 1]
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass
    for i in range(len(text)):
        if text[i] == "{":
            depth = 0
            for j in range(i, len(text)):
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[i : j + 1]
                        try:
                            json.loads(candidate)
                            return candidate
                        except json.JSONDecodeError:
                            break
    return None


def _get_required_criteria(level_number: int) -> list:
    criteria_map = {
        1: ["role_definition", "instruction_clarity", "goal_orientation"],
        2: ["output_format", "format_adherence", "parsability"],
        3: ["example_presence", "example_quality", "pattern_guidance"],
        4: ["step_decomposition", "sequential_logic", "intermediate_outputs"],
        5: ["injection_resistance", "edge_case_handling", "constraint_enforcement", "robustness"],
    }
    return criteria_map.get(level_number, criteria_map[1])


def _validate_grade_schema(data: dict, level_number: int) -> dict:
    required_criteria = _get_required_criteria(level_number)
    valid_grades = ["S", "A", "B", "C", "D"]
    grade = data.get("grade", "D")
    if grade not in valid_grades:
        grade = "D"
    verdict = data.get("verdict", "revise")
    if verdict not in ("pass", "revise"):
        verdict = "revise"

    normalized = {
        "understanding": data.get("understanding", "Could not determine prompt intent."),
        "grade": grade,
        "criteria": {},
        "overall_feedback": data.get("overall_feedback", "Evaluation incomplete."),
        "verdict": verdict,
        "line_analysis": [],
    }

    raw_criteria = data.get("criteria", {})
    for criterion in required_criteria:
        raw = raw_criteria.get(criterion, {})
        if not isinstance(raw, dict):
            raw = {}
        pass_val = raw.get("pass", False)
        if isinstance(pass_val, bool):
            pass_bool = pass_val
        elif isinstance(pass_val, str):
            pass_bool = pass_val.lower() in ("true", "yes", "pass")
        else:
            pass_bool = False
        normalized["criteria"][criterion] = {
            "pass": pass_bool,
            "weakness": raw.get("weakness", "") or "",
            "question": raw.get("question", "") or "",
        }

    raw_lines = data.get("line_analysis", [])
    if isinstance(raw_lines, list):
        for item in raw_lines:
            if isinstance(item, dict):
                normalized["line_analysis"].append({
                    "line_or_phrase": item.get("line_or_phrase", ""),
                    "issue": item.get("issue", ""),
                    "why_it_matters": item.get("why_it_matters", ""),
                    "severity": item.get("severity", "medium") if item.get("severity") in ("low", "medium", "high") else "medium",
                    "guiding_question": item.get("guiding_question", ""),
                })

    all_pass = all(c["pass"] for c in normalized["criteria"].values())
    if all_pass:
        normalized["verdict"] = "pass"
    else:
        normalized["verdict"] = "revise"

    return normalized


def _generate_line_analysis(prompt: str, criteria: dict, level_number: int) -> List[dict]:
    """Generate line-by-line analysis from failed criteria weaknesses."""
    lines = []
    for crit_name, crit_data in criteria.items():
        if not crit_data.get("pass", False) and crit_data.get("weakness"):
            lines.append({
                "line_or_phrase": crit_data["weakness"][:120] if len(crit_data["weakness"]) > 120 else crit_data["weakness"],
                "issue": f"Failed criterion: {crit_name.replace('_', ' ')}",
                "why_it_matters": _get_educational_note(level_number, crit_name),
                "severity": "high" if level_number >= 4 else "medium",
                "guiding_question": crit_data.get("question", "How can you improve this?"),
            })
    return lines


def _get_educational_note(level: int, criterion: str) -> str:
    notes = {
        1: {
            "role_definition": "Without a clear role, the AI has no persona to adopt, leading to generic responses.",
            "instruction_clarity": "Vague instructions force the AI to guess your intent, reducing output quality.",
            "goal_orientation": "Without a stated goal, the AI doesn't know what success looks like.",
        },
        2: {
            "output_format": "Unstructured output is unpredictable and hard to process programmatically.",
            "format_adherence": "Incomplete format specs leave room for interpretation and inconsistency.",
            "parsability": "If output can't be reliably parsed, it loses its value for automation.",
        },
        3: {
            "example_presence": "Examples are the most effective way to communicate output expectations.",
            "example_quality": "Poor examples can mislead the AI more than no examples at all.",
            "pattern_guidance": "Examples must clearly demonstrate the pattern, not just show random data.",
        },
        4: {
            "step_decomposition": "Complex tasks without decomposition overwhelm the AI's working memory.",
            "sequential_logic": "Illogical step ordering produces incorrect or incomplete results.",
            "intermediate_outputs": "Without checkpoints, errors propagate undetected through the entire output.",
        },
        5: {
            "injection_resistance": "Prompt injection is the #1 vulnerability in production LLM applications.",
            "edge_case_handling": "Ambiguous inputs will be exploited or produce incorrect outputs without guardrails.",
            "constraint_enforcement": "Without strict boundaries, the AI may operate outside your intended scope.",
            "robustness": "A non-robust prompt is brittle and fails under slight variations in input.",
        },
    }
    return notes.get(level, {}).get(criterion, "This criterion is critical for passing the current level.")


def _generate_fallback_grade(user_prompt: str, level_info: dict, domain: str, level_number: int) -> dict:
    """Generate a deterministic fallback grade when API is unavailable."""
    prompt_lower = user_prompt.lower()
    prompt_len = len(user_prompt.strip().split())
    required_criteria = _get_required_criteria(level_number)
    edu = LEVEL_EDUCATIONAL_NOTES.get(level_number, {})

    criteria = {}
    for criterion in required_criteria:
        criteria[criterion] = {"pass": False, "weakness": "", "question": ""}

    if level_number == 1:
        has_role = any(word in prompt_lower for word in ["act as", "role", "you are", "you're", "pretend", "expert", "specialist", "assistant"])
        criteria["role_definition"] = {
            "pass": has_role,
            "weakness": "" if has_role else "No role or persona defined for the AI. The prompt immediately starts with a task without establishing who the AI should be.",
            "question": "" if has_role else "What specific role should the AI assume? (e.g., 'Act as a senior software engineer')",
        }
        has_clear_instruction = prompt_len >= 5 and ("?" in user_prompt or user_prompt.strip().endswith("."))
        criteria["instruction_clarity"] = {
            "pass": has_clear_instruction,
            "weakness": "" if has_clear_instruction else "Instruction is too short or unclear. The AI cannot determine what specific task to perform.",
            "question": "" if has_clear_instruction else "What specific task do you want the AI to perform? Be precise about the desired output.",
        }
        has_goal = any(word in prompt_lower for word in ["goal", "objective", "purpose", "aim", "so that", "in order to"])
        criteria["goal_orientation"] = {
            "pass": has_goal,
            "weakness": "" if has_goal else "No clear goal or desired outcome stated. The AI doesn't know what success looks like.",
            "question": "" if has_goal else "What is the desired outcome of this prompt? What should the AI achieve?",
        }

    elif level_number == 2:
        has_format = any(word in prompt_lower for word in ["format", "json", "yaml", "xml", "csv", "table", "markdown", "list", "bullet", "output as", "respond with", "structure"])
        criteria["output_format"] = {
            "pass": has_format,
            "weakness": "" if has_format else "No output format specified. The AI will choose its own format, making outputs inconsistent.",
            "question": "" if has_format else "What format should the output follow? (e.g., JSON, markdown, table, CSV)",
        }
        has_detailed_format = len(re.findall(r"(format|json|yaml|xml|table)", prompt_lower)) >= 2
        criteria["format_adherence"] = {
            "pass": has_detailed_format,
            "weakness": "" if has_detailed_format else "Format description lacks detail. The AI might interpret the format differently than intended.",
            "question": "" if has_detailed_format else "How can you make the format instructions more precise? Include field names, types, or example structures.",
        }
        criteria["parsability"] = {
            "pass": has_format,
            "weakness": "" if has_format else "Output may be inconsistent and hard to parse programmatically.",
            "question": "" if has_format else "How can you ensure the output is consistently parseable? Consider using JSON with a defined schema.",
        }

    elif level_number == 3:
        has_example = bool(re.search(r"(example|for example|e\.g\.|for instance|such as|like this|sample|input:|output:)", prompt_lower))
        criteria["example_presence"] = {
            "pass": has_example,
            "weakness": "" if has_example else "No examples provided in the prompt. The AI must guess the expected output pattern.",
            "question": "" if has_example else "Can you include an example to demonstrate the expected input-output relationship?",
        }
        has_multiple_examples = prompt_lower.count("example") >= 2
        criteria["example_quality"] = {
            "pass": has_example and has_multiple_examples,
            "weakness": "" if (has_example and has_multiple_examples) else "Examples are insufficient or unclear." if has_example else "No examples to evaluate quality.",
            "question": "" if (has_example and has_multiple_examples) else "How can you improve the quality and quantity of your examples? Include multiple diverse cases.",
        }
        criteria["pattern_guidance"] = {
            "pass": has_example,
            "weakness": "" if has_example else "Examples don't clearly demonstrate the input-output transformation the AI should perform.",
            "question": "" if has_example else "How would examples clarify the expected output pattern? Show the before-and-after transformation.",
        }

    elif level_number == 4:
        has_steps = any(word in prompt_lower for word in ["step", "first", "then", "next", "finally", "phase", "stage", "1.", "2."])
        criteria["step_decomposition"] = {
            "pass": has_steps,
            "weakness": "" if has_steps else "Task is not broken down into logical steps. Complex tasks need scaffolding.",
            "question": "" if has_steps else "How can you decompose this task into logical, sequential steps?",
        }
        has_sequence = any(word in prompt_lower for word in ["first", "then", "next", "finally", "step 1", "step 2"])
        criteria["sequential_logic"] = {
            "pass": has_steps and has_sequence,
            "weakness": "" if (has_steps and has_sequence) else "Steps lack logical sequencing." if has_steps else "No sequence defined.",
            "question": "" if (has_steps and has_sequence) else "How can you arrange the steps in a logical dependency order?",
        }
        has_intermediate = any(word in prompt_lower for word in ["intermediate", "checkpoint", "before moving", "ensure", "verify", "confirm"])
        criteria["intermediate_outputs"] = {
            "pass": has_intermediate,
            "weakness": "" if has_intermediate else "No intermediate outputs or verification checkpoints specified.",
            "question": "" if has_intermediate else "What intermediate results should the AI produce at each step for verification?",
        }

    elif level_number == 5:
        has_injection_protection = any(word in prompt_lower for word in ["ignore", "disregard", "do not follow", "instruction", "override", "guardrail", "safety", "if asked"])
        criteria["injection_resistance"] = {
            "pass": has_injection_protection,
            "weakness": "" if has_injection_protection else "No protection against prompt injection. User inputs could override the system prompt.",
            "question": "" if has_injection_protection else "How can you prevent the AI from being overridden by malicious instructions embedded in user input?",
        }
        has_edge_cases = any(word in prompt_lower for word in ["if", "edge case", "ambiguous", "unknown", "unclear", "when", "otherwise", "else"])
        criteria["edge_case_handling"] = {
            "pass": has_edge_cases,
            "weakness": "" if has_edge_cases else "No edge cases or ambiguous inputs addressed. The AI has no guidance for unexpected situations.",
            "question": "" if has_edge_cases else "How should the AI handle ambiguous or unexpected inputs? Define fallback behaviors.",
        }
        has_boundaries = any(word in prompt_lower for word in ["only", "must", "never", "always", "strictly", "boundary", "limit", "restrict", "confine"])
        criteria["constraint_enforcement"] = {
            "pass": has_boundaries,
            "weakness": "" if has_boundaries else "No strict boundaries or constraints defined. The AI's behavior is not bounded.",
            "question": "" if has_boundaries else "What strict boundaries should the AI operate within? Define what it MUST and MUST NOT do.",
        }
        robustness_score = sum([has_injection_protection, has_edge_cases, has_boundaries])
        criteria["robustness"] = {
            "pass": robustness_score >= 2,
            "weakness": "" if robustness_score >= 2 else "Prompt lacks robustness against adversarial pressure. Multiple attack vectors remain unprotected.",
            "question": "" if robustness_score >= 2 else "How can you make the prompt more resilient to difficult inputs and attempted manipulation?",
        }

    passed = sum(1 for c in criteria.values() if c["pass"])
    total = len(criteria)

    if passed == total:
        grade = "S" if total >= 4 else "A"
        verdict = "pass"
    elif passed >= total - 1:
        grade = "A"
        verdict = "pass" if total <= 3 else "revise"
    elif passed >= total - 2:
        grade = "B"
        verdict = "revise"
    elif passed >= 1:
        grade = "C"
        verdict = "revise"
    else:
        grade = "D"
        verdict = "revise"

    line_analysis = _generate_line_analysis(user_prompt, criteria, level_number)

    coach_tip = edu.get("coach_tip", "")
    principle = edu.get("principle", "")
    why_rejected = edu.get("why_rejected", "")

    return {
        "understanding": f"The prompt attempts to: '{user_prompt[:150]}...'",
        "grade": grade,
        "criteria": criteria,
        "overall_feedback": f"**Principle:** {principle}\n\n**Why rejected:** {why_rejected}\n\n**Coach's Tip:** {coach_tip}\n\n**Result:** {passed}/{total} criteria passed.",
        "verdict": verdict,
        "line_analysis": line_analysis,
    }


def get_educational_context(level_number: int) -> dict:
    """Get educational coaching context for a level."""
    return LEVEL_EDUCATIONAL_NOTES.get(level_number, {})


def grade_prompt(
    user_prompt: str,
    level_number: int = 1,
    domain: str = "general",
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> dict:
    from levels import get_level

    level_info = get_level(level_number)
    api_key = api_key or os.getenv("OPENROUTER_API_KEY")
    level_criteria = _build_level_criteria(level_number)

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        level_name=level_info["name"],
        level_label=level_info.get("difficulty_label", "Unknown"),
        level_description=level_info["description"],
        evaluation_focus="; ".join(level_info.get("evaluation_focus", [])),
        domain=domain,
        level_criteria=level_criteria,
    )

    user_message = (
        f"Evaluate this prompt for Level {level_number} - {level_info['name']} (Domain: {domain}).\n"
        f"Level requirement: {level_info['pass_condition']}\n\n"
        f"PROMPT TO EVALUATE:\n{user_prompt}"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.0,
        "max_tokens": 2000,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://prompt-doctor.app",
        "X-Title": "Prompt Doctor",
    }

    last_error = None
    for attempt in range(1 + MAX_RETRIES):
        try:
            response = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            response_data = response.json()
            choices = response_data.get("choices", [])
            if not choices:
                raise ValueError("No choices in API response")
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                raise ValueError("Empty content in API response")
            json_str = _extract_json_from_text(content)
            if json_str is None:
                raise ValueError(f"No valid JSON found")
            parsed = json.loads(json_str)
            normalized = _validate_grade_schema(parsed, level_number)
            return normalized
        except requests.exceptions.Timeout:
            last_error = f"Request timed out after {TIMEOUT_SECONDS}s"
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            last_error = f"Request failed: {str(e)}"
            time.sleep(2)
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            last_error = f"Response parsing error: {str(e)}"
            if attempt < MAX_RETRIES and "No valid JSON" in str(e):
                time.sleep(1)
            else:
                break

    return _generate_fallback_grade(user_prompt, level_info, domain, level_number)


def grade_prompt_raw(
    user_prompt: str,
    level_number: int = 1,
    domain: str = "general",
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    result = grade_prompt(user_prompt, level_number, domain, api_key, model)
    return json.dumps(result, indent=2, ensure_ascii=False)