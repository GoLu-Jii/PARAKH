"""Seed approved content to database (Phase 1 minimal seed).

Idempotent seed script that creates:
- 5 fixed V1 topics
- Development content for DSA only (3 concepts, 3 questions, 9 follow-ups)
"""

import asyncio
from pathlib import Path
import sys

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import func, select
from app.db.models import Concept, FollowUp, Question, Topic
from app.db.session import AsyncSessionLocal


TOPICS_DATA = [
    "DSA",
    "Operating Systems",
    "DBMS",
    "Computer Networks",
    "System Design",
]

DSA_SEED_CONTENT = [
    {
        "concept_name": "Arrays & Hash Map Lookup",
        "cognitive_level": 2,
        "questions": [
            {
                "question_text": "Explain how a Hash Map provides constant-time average lookups compared to searching an unsorted array, and what happens when hash collisions occur.",
                "expected_concepts": [
                    "Hash function maps keys to array indices",
                    "Average time complexity is O(1) for insert and lookup",
                    "Collision handling using chaining or open addressing",
                    "Worst-case degrades to O(N) when collisions proliferate",
                ],
                "follow_ups": [
                    {
                        "follow_up_text": "What specific collision resolution strategies exist when two keys hash to the same index, and how do they impact performance?",
                        "targets_gap": "Collision handling using chaining or open addressing",
                    },
                    {
                        "follow_up_text": "Under what conditions does a Hash Map lookup degrade from O(1) average time to O(N) worst-case time?",
                        "targets_gap": "Worst-case degrades to O(N) when collisions proliferate",
                    },
                    {
                        "follow_up_text": "How does the underlying hash function determine the array index for a given key?",
                        "targets_gap": "Hash function maps keys to array indices",
                    },
                ],
            }
        ],
    },
    {
        "concept_name": "Two-Pointer Technique & Sliding Window",
        "cognitive_level": 4,
        "questions": [
            {
                "question_text": "How does the two-pointer approach optimize searching for pair sums in a sorted array compared to a naive nested loop?",
                "expected_concepts": [
                    "Sorted order enables directional pointer movement based on comparison with target sum",
                    "Reduces time complexity from O(N^2) to O(N)",
                    "Left pointer increments when sum is too small, right pointer decrements when sum is too large",
                    "Requires array to be pre-sorted or costs O(N log N) sorting step",
                ],
                "follow_ups": [
                    {
                        "follow_up_text": "Why must the array be sorted for the two-pointer directional movement logic to guarantee finding the pair?",
                        "targets_gap": "Sorted order enables directional pointer movement based on comparison with target sum",
                    },
                    {
                        "follow_up_text": "How exactly do you decide which pointer to move when the current sum is less than or greater than the target sum?",
                        "targets_gap": "Left pointer increments when sum is too small, right pointer decrements when sum is too large",
                    },
                    {
                        "follow_up_text": "What is the time complexity improvement of two pointers over the brute-force nested loop approach?",
                        "targets_gap": "Reduces time complexity from O(N^2) to O(N)",
                    },
                ],
            }
        ],
    },
    {
        "concept_name": "Trade-offs of In-Place vs Auxiliary Space Algorithms",
        "cognitive_level": 6,
        "questions": [
            {
                "question_text": "Compare in-place array manipulation algorithms with methods that use auxiliary storage. What are the memory trade-offs and risks involved in modifying input data in-place?",
                "expected_concepts": [
                    "In-place algorithms achieve O(1) auxiliary space complexity",
                    "Modifying input in-place risks side-effects for callers sharing references",
                    "Using auxiliary space preserves original data immutability",
                    "Trade-off between memory footprint reduction and thread safety or data integrity",
                ],
                "follow_ups": [
                    {
                        "follow_up_text": "What auxiliary space complexity does an in-place algorithm achieve compared to copying data?",
                        "targets_gap": "In-place algorithms achieve O(1) auxiliary space complexity",
                    },
                    {
                        "follow_up_text": "What potential software engineering risks or bugs arise when mutating input parameters in-place?",
                        "targets_gap": "Modifying input in-place risks side-effects for callers sharing references",
                    },
                    {
                        "follow_up_text": "How do you evaluate the trade-off between strict data immutability and memory optimization in system design?",
                        "targets_gap": "Trade-off between memory footprint reduction and thread safety or data integrity",
                    },
                ],
            }
        ],
    },
]


async def seed_database():
    async with AsyncSessionLocal() as session:
        # 1. Seed Topics
        topic_map = {}
        for topic_name in TOPICS_DATA:
            stmt = select(Topic).where(Topic.name == topic_name)
            res = await session.execute(stmt)
            topic = res.scalar_one_or_none()
            if not topic:
                topic = Topic(name=topic_name)
                session.add(topic)
                await session.flush()
            topic_map[topic_name] = topic

        # 2. Seed DSA Content
        dsa_topic = topic_map["DSA"]
        for concept_data in DSA_SEED_CONTENT:
            stmt = select(Concept).where(
                Concept.topic_id == dsa_topic.id,
                Concept.name == concept_data["concept_name"],
            )
            res = await session.execute(stmt)
            concept = res.scalar_one_or_none()
            if not concept:
                concept = Concept(
                    topic_id=dsa_topic.id,
                    name=concept_data["concept_name"],
                    cognitive_level=concept_data["cognitive_level"],
                )
                session.add(concept)
                await session.flush()

            for q_data in concept_data["questions"]:
                stmt = select(Question).where(
                    Question.concept_id == concept.id,
                    Question.question_text == q_data["question_text"],
                )
                res = await session.execute(stmt)
                question = res.scalar_one_or_none()
                if not question:
                    question = Question(
                        concept_id=concept.id,
                        question_text=q_data["question_text"],
                        expected_concepts=q_data["expected_concepts"],
                        is_llm_generated=False,
                    )
                    session.add(question)
                    await session.flush()

                for fu_data in q_data["follow_ups"]:
                    stmt = select(FollowUp).where(
                        FollowUp.question_id == question.id,
                        FollowUp.follow_up_text == fu_data["follow_up_text"],
                    )
                    res = await session.execute(stmt)
                    follow_up = res.scalar_one_or_none()
                    if not follow_up:
                        follow_up = FollowUp(
                            question_id=question.id,
                            follow_up_text=fu_data["follow_up_text"],
                            targets_gap=fu_data["targets_gap"],
                        )
                        session.add(follow_up)

        await session.commit()

        # 3. Verification Queries & Summary
        topic_count = (await session.execute(select(func.count(Topic.id)))).scalar()
        dsa_concept_count = (
            await session.execute(
                select(func.count(Concept.id)).where(Concept.topic_id == dsa_topic.id)
            )
        ).scalar()
        dsa_question_count = (
            await session.execute(
                select(func.count(Question.id))
                .join(Concept)
                .where(Concept.topic_id == dsa_topic.id)
            )
        ).scalar()
        dsa_followup_count = (
            await session.execute(
                select(func.count(FollowUp.id))
                .join(Question)
                .join(Concept)
                .where(Concept.topic_id == dsa_topic.id)
            )
        ).scalar()
        other_concept_count = (
            await session.execute(
                select(func.count(Concept.id)).where(Concept.topic_id != dsa_topic.id)
            )
        ).scalar()

        print("--- Database Seed Summary ---")
        print(f"Topics: {topic_count}")
        print(f"DSA concepts: {dsa_concept_count}")
        print(f"DSA questions: {dsa_question_count}")
        print(f"DSA follow-ups: {dsa_followup_count}")
        print(f"Other topic concepts: {other_concept_count}")


if __name__ == "__main__":
    asyncio.run(seed_database())
