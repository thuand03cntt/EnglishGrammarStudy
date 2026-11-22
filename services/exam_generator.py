import random
from typing import List, Optional, Tuple
from sqlalchemy import or_, and_, desc
from models import db, Question, Level, Category, ExamAttempt, ExamAttemptDetail, User

def generate_exam_questions(
    user: User,
    selected_category_id: Optional[int] = None,
    question_count: int = 10
) -> Tuple[List[Question], dict]:
    """
    Intelligent Question Selector Algorithm:
    1. Filter by category (category + all subcategories + general questions where category_id is NULL).
    2. Filter by user level rank (rank <= user_level_rank, can expand to user_level_rank + 1 if needed,
       strictly preventing Intermediate/Advance questions for Beginner users).
    3. Partition into 3 priority groups:
       - Group 1 (Highest): Questions user answered WRONG on most recent attempt + UNSEEN questions.
       - Group 2 (Medium): Questions user answered CORRECTLY in older attempts.
       - Group 3 (Lowest): Questions user answered CORRECTLY recently.
    4. Randomly shuffle each group and collect up to `question_count` questions.
    
    Returns:
        (selected_questions, debug_stats)
    """
    # 1. Resolve user rank (Default to 1 - Beginner if no level set)
    user_level_rank = 1
    if user.level and user.level.rank_order:
        user_level_rank = user.level.rank_order

    # 2. Category filtering logic
    valid_category_ids = []
    has_category_filter = False

    if selected_category_id and selected_category_id > 0:
        has_category_filter = True
        valid_category_ids.append(selected_category_id)
        # Include all subcategories of selected category
        subcategories = Category.query.filter_by(parent_id=selected_category_id).all()
        for sub in subcategories:
            valid_category_ids.append(sub.id)

    # Base query joined with Level
    base_query = db.session.query(Question).join(Level, Question.level_id == Level.id)

    if has_category_filter:
        # Category specific questions + General questions (category_id is NULL)
        base_query = base_query.filter(
            or_(
                Question.category_id.in_(valid_category_ids),
                Question.category_id.is_(None)
            )
        )

    # 3. Level filtering logic
    # Initial strictly <= user_level_rank
    strict_level_query = base_query.filter(Level.rank_order <= user_level_rank)
    candidate_questions = strict_level_query.all()

    # If count is less than requested, check if expansion is allowed
    # Constraint: Never give Intermediate (rank 4) or Advance (rank 5) to Beginner (rank 1)
    if len(candidate_questions) < question_count:
        if user_level_rank == 1:
            max_rank = 2  # Max Elementary for Beginner
        else:
            max_rank = min(user_level_rank + 1, 5)

        expanded_query = base_query.filter(Level.rank_order <= max_rank)
        candidate_questions = expanded_query.all()

    # If still empty (e.g. no questions at all in DB for criteria), fallback to all within allowed level
    if not candidate_questions:
        candidate_questions = db.session.query(Question).join(Level).filter(
            Level.rank_order <= (2 if user_level_rank == 1 else min(user_level_rank + 1, 5))
        ).all()

    # Total available candidate questions
    candidate_map = {q.id: q for q in candidate_questions}
    candidate_ids = set(candidate_map.keys())

    if not candidate_ids:
        return [], {"error": "No questions available matching criteria."}

    # 4. Analyze User History for Priority Grouping
    # Find user's past completed attempts
    completed_attempts = ExamAttempt.query.filter(
        ExamAttempt.user_id == user.id,
        ExamAttempt.completed_at.isnot(None)
    ).order_by(desc(ExamAttempt.completed_at), desc(ExamAttempt.id)).all()

    # Identify recent attempts (top 3 most recent attempts)
    recent_attempt_ids = {att.id for att in completed_attempts[:3]}

    # Map question_id -> list of attempts details (ordered latest to oldest)
    user_attempt_details = (
        db.session.query(ExamAttemptDetail, ExamAttempt.completed_at, ExamAttempt.id)
        .join(ExamAttempt, ExamAttemptDetail.attempt_id == ExamAttempt.id)
        .filter(
            ExamAttempt.user_id == user.id,
            ExamAttempt.completed_at.isnot(None),
            ExamAttemptDetail.question_id.in_(candidate_ids)
        )
        .order_by(desc(ExamAttempt.completed_at), desc(ExamAttempt.id))
        .all()
    )

    history_by_question = {}
    for detail, completed_at, att_id in user_attempt_details:
        qid = detail.question_id
        if qid not in history_by_question:
            history_by_question[qid] = []
        history_by_question[qid].append({
            "is_correct": detail.is_correct,
            "attempt_id": att_id,
            "completed_at": completed_at
        })

    group_1 = []  # High: Never seen OR Last attempt was WRONG
    group_2 = []  # Medium: Answered correct in older attempts
    group_3 = []  # Low: Answered correct recently (in recent 3 attempts)

    for qid in candidate_ids:
        question = candidate_map[qid]
        if qid not in history_by_question:
            # Never attempted
            group_1.append(question)
        else:
            attempts = history_by_question[qid]
            latest_attempt = attempts[0]
            if not latest_attempt["is_correct"]:
                # Most recent attempt on this question was WRONG
                group_1.append(question)
            else:
                # Most recent was correct. Check if in recent attempts or older
                if latest_attempt["attempt_id"] in recent_attempt_ids:
                    group_3.append(question)
                else:
                    group_2.append(question)

    # 5. Shuffle each group independently
    random.shuffle(group_1)
    random.shuffle(group_2)
    random.shuffle(group_3)

    # 6. Fill up to question_count
    selected: List[Question] = []

    # Priority 1
    needed = question_count - len(selected)
    selected.extend(group_1[:needed])

    # Priority 2
    if len(selected) < question_count:
        needed = question_count - len(selected)
        selected.extend(group_2[:needed])

    # Priority 3
    if len(selected) < question_count:
        needed = question_count - len(selected)
        selected.extend(group_3[:needed])

    # Final shuffle so that questions of different groups are organically mixed
    random.shuffle(selected)

    debug_stats = {
        "user_level_rank": user_level_rank,
        "candidate_total": len(candidate_questions),
        "group_1_count": len(group_1),
        "group_2_count": len(group_2),
        "group_3_count": len(group_3),
        "selected_count": len(selected)
    }

    return selected, debug_stats
