from app.db.models.question import Question


def select_next_question(
    candidate_questions: list[Question],
    question_ids_already_asked: list[int],
    concept_states: dict[int, str],
) -> Question | None:
    """Deterministically selects the next question for a session based on concept state.

    Ranking Order:
    1. Weak concepts first (status == 'weak')
    2. Unseen concepts second (status == 'not_seen' or missing)
    3. Cleared concepts last (status == 'cleared')

    Excludes any question ID present in question_ids_already_asked.
    Pure Python logic — no LLM or network calls.
    """
    already_asked_set = set(question_ids_already_asked)
    remaining_candidates = [
        q for q in candidate_questions if q.id not in already_asked_set
    ]

    if not remaining_candidates:
        return None

    def get_rank(q: Question) -> tuple[int, int]:
        status = concept_states.get(q.concept_id, "not_seen")
        if status == "weak":
            priority = 0
        elif status == "not_seen":
            priority = 1
        else:
            priority = 2
        return (priority, q.id)

    remaining_candidates.sort(key=get_rank)
    return remaining_candidates[0]
