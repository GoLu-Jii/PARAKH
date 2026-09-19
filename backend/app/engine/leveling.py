def evaluate_level_outcome(scores: list[float]) -> str:
    """Evaluates level advancement outcome based on the 4 main-question scores.

    Rules:
    - average(scores) >= 7.0 AND min(scores) >= 4.0 -> 'level_up'
    - Otherwise -> 'same'

    Pure Python logic — no LLM or network calls.
    """
    if not scores or len(scores) < 4:
        return "same"

    main_scores = scores[:4]
    avg_score = sum(main_scores) / len(main_scores)
    min_score = min(main_scores)

    if avg_score >= 7.0 and min_score >= 4.0:
        return "level_up"
    return "same"


def compute_next_level(current_level: int, target_level: int, outcome: str) -> int:
    """Computes updated level for a student topic progress row.

    Handles normal +1 progression and level-skip jumping.
    Max level is 10.
    """
    if outcome != "level_up":
        return current_level

    if target_level > current_level:
        return min(10, target_level)
    return min(10, current_level + 1)
