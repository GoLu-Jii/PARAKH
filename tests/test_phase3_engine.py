import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from datetime import datetime
from zoneinfo import ZoneInfo
from app.db.models.concept import Concept
from app.db.models.question import Question
from app.engine.leveling import compute_next_level, evaluate_level_outcome
from app.engine.selection import select_next_question
from app.engine.session_flow import get_interview_day_bounds


def test_leveling_outcomes():
    # 7, 7, 7, 7 -> level_up
    assert evaluate_level_outcome([7.0, 7.0, 7.0, 7.0]) == "level_up"

    # 10, 10, 10, 3 -> same (min score < 4.0)
    assert evaluate_level_outcome([10.0, 10.0, 10.0, 3.0]) == "same"

    # 6, 7, 8, 9 -> level_up (avg = 7.5 >= 7.0, min = 6.0 >= 4.0)
    assert evaluate_level_outcome([6.0, 7.0, 8.0, 9.0]) == "level_up"

    # 6, 6, 6, 6 -> same (avg = 6.0 < 7.0)
    assert evaluate_level_outcome([6.0, 6.0, 6.0, 6.0]) == "same"

    # Fewer than 4 scores -> same
    assert evaluate_level_outcome([10.0, 10.0, 10.0]) == "same"

    print("Leveling evaluation tests PASSED.")


def test_level_progression():
    # Normal +1 level_up
    assert compute_next_level(current_level=1, target_level=1, outcome="level_up") == 2
    assert compute_next_level(current_level=3, target_level=3, outcome="level_up") == 4

    # Level skip attempt
    assert compute_next_level(current_level=1, target_level=5, outcome="level_up") == 5

    # Same outcome
    assert compute_next_level(current_level=2, target_level=2, outcome="same") == 2
    assert compute_next_level(current_level=1, target_level=4, outcome="same") == 1

    # Cap at level 10
    assert compute_next_level(current_level=10, target_level=10, outcome="level_up") == 10
    print("Level progression tests PASSED.")


def test_deterministic_question_selection():
    # Create mock questions attached to concepts
    c_weak = Concept(id=1, topic_id=1, cognitive_level=2)
    c_unseen = Concept(id=2, topic_id=1, cognitive_level=2)
    c_cleared = Concept(id=3, topic_id=1, cognitive_level=2)

    q_weak = Question(id=101, concept_id=1, concept=c_weak)
    q_unseen = Question(id=102, concept_id=2, concept=c_unseen)
    q_cleared = Question(id=103, concept_id=3, concept=c_cleared)

    candidates = [q_cleared, q_unseen, q_weak]
    concept_states = {1: "weak", 2: "not_seen", 3: "cleared"}

    # Weak concept (q_weak) should be selected first
    selected1 = select_next_question(candidates, [], concept_states)
    assert selected1.id == 101, f"Expected 101, got {selected1.id}"

    # Once q_weak is asked, unseen (q_unseen) should be selected second
    selected2 = select_next_question(candidates, [101], concept_states)
    assert selected2.id == 102, f"Expected 102, got {selected2.id}"

    # Once 101 and 102 asked, cleared (q_cleared) selected third
    selected3 = select_next_question(candidates, [101, 102], concept_states)
    assert selected3.id == 103, f"Expected 103, got {selected3.id}"

    # Pool exhausted
    selected4 = select_next_question(candidates, [101, 102, 103], concept_states)
    assert selected4 is None
    print("Deterministic question selection tests PASSED.")


def test_timezone_interview_day_bounds():
    # Test at 2:00 AM Kolkata time on 2026-09-19
    dt_2am = datetime(2026, 9, 19, 2, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    dt_2am_utc = dt_2am.astimezone(ZoneInfo("UTC"))

    start_utc, end_utc = get_interview_day_bounds("Asia/Kolkata", dt_2am_utc)

    # 2 AM on Sep 19 belongs to interview day starting 4 AM on Sep 18 and ending 4 AM on Sep 19
    start_local = start_utc.astimezone(ZoneInfo("Asia/Kolkata"))
    end_local = end_utc.astimezone(ZoneInfo("Asia/Kolkata"))

    assert start_local.year == 2026 and start_local.month == 9 and start_local.day == 18 and start_local.hour == 4
    assert end_local.year == 2026 and end_local.month == 9 and end_local.day == 19 and end_local.hour == 4

    # Test at 10:00 AM Kolkata time on 2026-09-19
    dt_10am = datetime(2026, 9, 19, 10, 0, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    dt_10am_utc = dt_10am.astimezone(ZoneInfo("UTC"))

    start_utc2, end_utc2 = get_interview_day_bounds("Asia/Kolkata", dt_10am_utc)
    start_local2 = start_utc2.astimezone(ZoneInfo("Asia/Kolkata"))
    end_local2 = end_utc2.astimezone(ZoneInfo("Asia/Kolkata"))

    assert start_local2.year == 2026 and start_local2.month == 9 and start_local2.day == 19 and start_local2.hour == 4
    assert end_local2.year == 2026 and end_local2.month == 9 and end_local2.day == 20 and end_local2.hour == 4

    print("Timezone interview day bounds tests PASSED.")


if __name__ == "__main__":
    test_leveling_outcomes()
    test_level_progression()
    test_deterministic_question_selection()
    test_timezone_interview_day_bounds()
