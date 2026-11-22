from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import func, desc

from models import db, User, Level, Category, Question, ExamAttempt, ExamAttemptDetail
from services.exam_generator import generate_exam_questions

exam_bp = Blueprint("exam", __name__)

@exam_bp.route("/")
def index():
    """
    Home page & Leaderboard.
    Ranks candidates based on total accumulated correct answers across all completed attempts.
    """
    # Query leaderboard: Top candidates ordered by total correct answers
    leaderboard_query = (
        db.session.query(
            User.id,
            User.username,
            User.avatar,
            Level.name.label("level_name"),
            func.count(func.distinct(ExamAttempt.id)).label("total_attempts"),
            func.coalesce(func.sum(ExamAttempt.correct_count), 0).label("total_correct")
        )
        .outerjoin(Level, User.level_id == Level.id)
        .join(ExamAttempt, (User.id == ExamAttempt.user_id) & (ExamAttempt.completed_at.isnot(None)))
        .filter(User.is_admin.is_(False))
        .group_by(User.id, User.username, User.avatar, Level.name)
        .order_by(desc("total_correct"), desc("total_attempts"))
        .limit(10)
        .all()
    )

    # General statistics for dashboard cards
    total_questions = Question.query.count()
    total_exams_taken = ExamAttempt.query.filter(ExamAttempt.completed_at.isnot(None)).count()
    total_users = User.query.filter_by(is_admin=False).count()

    return render_template(
        "home/index.html",
        leaderboard=leaderboard_query,
        total_questions=total_questions,
        total_exams_taken=total_exams_taken,
        total_users=total_users
    )


@exam_bp.route("/exam/setup", methods=["GET", "POST"])
@login_required
def setup():
    """
    Configure and launch a new exam attempt:
    - Primary topic (cấp 1)
    - Sub-topic (cấp 2, optional)
    - Number of questions: 10, 20, 50, 100
    """
    if request.method == "POST":
        parent_category_id = request.form.get("parent_category_id", type=int)
        sub_category_id = request.form.get("sub_category_id", type=int)
        question_count = request.form.get("question_count", default=10, type=int)

        if question_count not in (10, 20, 50, 100):
            question_count = 10

        # Selected category logic: subcategory has precedence if picked
        selected_category_id = sub_category_id if (sub_category_id and sub_category_id > 0) else parent_category_id

        # Generate questions using intelligent selection algorithm
        selected_questions, stats = generate_exam_questions(
            user=current_user,
            selected_category_id=selected_category_id,
            question_count=question_count
        )

        if not selected_questions:
            flash(
                "Kho câu hỏi hiện tại chưa có câu hỏi nào phù hợp với chủ đề và trình độ của bạn. "
                "Vui lòng chọn chủ đề khác hoặc liên hệ quản trị viên.",
                "warning"
            )
            return redirect(url_for("exam.setup"))

        # Determine attempt number for this user
        last_attempt = (
            ExamAttempt.query.filter_by(user_id=current_user.id)
            .order_by(desc(ExamAttempt.attempt_number))
            .first()
        )
        attempt_number = (last_attempt.attempt_number + 1) if last_attempt else 1

        # Create new ExamAttempt
        new_attempt = ExamAttempt(
            user_id=current_user.id,
            category_id=selected_category_id if selected_category_id and selected_category_id > 0 else None,
            attempt_number=attempt_number,
            total_questions=len(selected_questions),
            started_at=datetime.now(timezone.utc)
        )
        db.session.add(new_attempt)
        db.session.flush()  # to obtain new_attempt.id

        # Add attempt details for each selected question
        for order_idx, q in enumerate(selected_questions, start=1):
            detail = ExamAttemptDetail(
                attempt_id=new_attempt.id,
                question_id=q.id,
                question_order=order_idx,
                is_correct=False
            )
            db.session.add(detail)

        db.session.commit()
        return redirect(url_for("exam.take", attempt_id=new_attempt.id))

    # GET: Load parent categories (parent_id IS NULL)
    parent_categories = Category.query.filter_by(parent_id=None).order_by(Category.name).all()
    all_categories = Category.query.order_by(Category.name).all()

    return render_template(
        "exam/setup.html",
        parent_categories=parent_categories,
        all_categories=all_categories
    )


@exam_bp.route("/api/categories/<int:parent_id>/subcategories")
def get_subcategories(parent_id):
    """API endpoint to fetch subcategories for dynamic dropdowns."""
    subcategories = Category.query.filter_by(parent_id=parent_id).order_by(Category.name).all()
    return jsonify([
        {"id": sub.id, "name": sub.name, "description": sub.description or ""}
        for sub in subcategories
    ])


@exam_bp.route("/exam/take/<int:attempt_id>")
@login_required
def take(attempt_id):
    """
    Exam taking interface:
    - Real-time countdown / elapsed timer
    - Pagination: 10 questions per page
    - Preserves answers across page transitions
    - Side navigation question palette
    """
    attempt = ExamAttempt.query.get_or_404(attempt_id)

    if attempt.user_id != current_user.id:
        abort(403)

    if attempt.is_completed:
        flash("Bài thi này đã được nộp và chấm điểm.", "info")
        return redirect(url_for("exam.result", attempt_id=attempt.id))

    # Retrieve all ordered question details
    details = ExamAttemptDetail.query.filter_by(attempt_id=attempt.id)\
        .order_by(ExamAttemptDetail.question_order).all()

    return render_template(
        "exam/take.html",
        attempt=attempt,
        details=details
    )


@exam_bp.route("/exam/submit/<int:attempt_id>", methods=["POST"])
@login_required
def submit(attempt_id):
    """
    Grade submitted exam:
    - Score = round((correct_count / total_questions) * 100, 2)
    - Records detailed choices & correctness
    - Updates duration_seconds and completed_at
    """
    attempt = ExamAttempt.query.get_or_404(attempt_id)

    if attempt.user_id != current_user.id:
        abort(403)

    if attempt.is_completed:
        return redirect(url_for("exam.result", attempt_id=attempt.id))

    # Read submitted duration (seconds) or calculate from start time
    submitted_duration = request.form.get("duration_seconds", type=int)
    if not submitted_duration or submitted_duration < 0:
        elapsed = datetime.now(timezone.utc) - attempt.started_at.replace(tzinfo=timezone.utc)
        submitted_duration = max(1, int(elapsed.total_seconds()))

    details = ExamAttemptDetail.query.filter_by(attempt_id=attempt.id).all()
    correct_count = 0
    wrong_count = 0

    for detail in details:
        # Form field name: answer_{detail.id} or question_{detail.question_id}
        ans_val = request.form.get(f"q_{detail.id}") or request.form.get(f"question_{detail.question_id}")
        selected_option = int(ans_val) if ans_val and ans_val in ("1", "2", "3", "4") else None

        detail.selected_option = selected_option
        if selected_option is not None and selected_option == detail.question.correct_option:
            detail.is_correct = True
            correct_count += 1
        else:
            detail.is_correct = False
            wrong_count += 1

    total_q = attempt.total_questions or len(details)
    score = round((correct_count / total_q) * 100, 2) if total_q > 0 else 0.0

    attempt.correct_count = correct_count
    attempt.wrong_count = wrong_count
    attempt.score = score
    attempt.duration_seconds = submitted_duration
    attempt.completed_at = datetime.now(timezone.utc)

    db.session.commit()
    flash("Nộp bài thi thành công! Xem kết quả chi tiết bên dưới.", "success")
    return redirect(url_for("exam.result", attempt_id=attempt.id))


@exam_bp.route("/exam/result/<int:attempt_id>")
@login_required
def result(attempt_id):
    """
    Exam result screen:
    - Score on 100-scale
    - Total correct / total wrong (highlighted red)
    - Duration taken
    - Explanations for all questions
    """
    attempt = ExamAttempt.query.get_or_404(attempt_id)

    if attempt.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    if not attempt.is_completed:
        return redirect(url_for("exam.take", attempt_id=attempt.id))

    details = ExamAttemptDetail.query.filter_by(attempt_id=attempt.id)\
        .order_by(ExamAttemptDetail.question_order).all()

    return render_template(
        "exam/result.html",
        attempt=attempt,
        details=details
    )


@exam_bp.route("/exam/history")
@login_required
def history():
    """History of all exam attempts by current user."""
    page = request.args.get("page", 1, type=int)
    attempts_pagination = (
        ExamAttempt.query.filter(
            ExamAttempt.user_id == current_user.id,
            ExamAttempt.completed_at.isnot(None)
        )
        .order_by(desc(ExamAttempt.completed_at))
        .paginate(page=page, per_page=10, error_out=False)
    )

    return render_template(
        "exam/history.html",
        pagination=attempts_pagination
    )


@exam_bp.route("/exam/review/<int:attempt_id>")
@login_required
def review(attempt_id):
    """Detailed review of a past attempt with green/red highlights and explanations."""
    attempt = ExamAttempt.query.get_or_404(attempt_id)

    if attempt.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    details = ExamAttemptDetail.query.filter_by(attempt_id=attempt.id)\
        .order_by(ExamAttemptDetail.question_order).all()

    return render_template(
        "exam/review.html",
        attempt=attempt,
        details=details
    )
