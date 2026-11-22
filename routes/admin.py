from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort
from flask_login import login_required, current_user
from sqlalchemy import or_, desc

from models import db, User, Level, Category, Question, ExamAttempt
from services.excel_service import generate_excel_template, import_questions_from_excel
from services.seed_data import seed_all_initial_data

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(f):
    """Ensures current user is logged in and possesses administrator privileges."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Bạn không có quyền truy cập vào phân hệ Quản trị viên.", "danger")
            return redirect(url_for("exam.index"))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    """Admin Dashboard overview metrics."""
    total_users = User.query.filter_by(is_admin=False).count()
    total_questions = Question.query.count()
    total_categories = Category.query.count()
    total_attempts = ExamAttempt.query.filter(ExamAttempt.completed_at.isnot(None)).count()
    
    recent_attempts = (
        ExamAttempt.query.filter(ExamAttempt.completed_at.isnot(None))
        .order_by(desc(ExamAttempt.completed_at))
        .limit(8)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_questions=total_questions,
        total_categories=total_categories,
        total_attempts=total_attempts,
        recent_attempts=recent_attempts
    )


@admin_bp.route("/seed-sample-data", methods=["GET", "POST"])
@admin_required
def seed_sample_data():
    """Manual trigger to seed or re-seed default categories, levels, and 30 sample questions."""
    seed_all_initial_data()
    flash("Tuyệt vời! Đã nạp thành công bộ danh mục Chủ đề 2 cấp và 30 câu hỏi ngữ pháp tiếng Anh mẫu có sẵn vào hệ thống.", "success")
    ref = request.referrer
    if ref and "/admin" in ref:
        return redirect(ref)
    return redirect(url_for("admin.questions"))


@admin_bp.route("/change-password", methods=["GET", "POST"])
@admin_required
def change_password():
    """Change Admin Password."""
    if request.method == "POST":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not current_user.check_password(old_password):
            flash("Mật khẩu hiện tại không đúng.", "danger")
            return render_template("admin/change_password.html")

        if len(new_password) < 6:
            flash("Mật khẩu mới phải có tối thiểu 6 ký tự.", "danger")
            return render_template("admin/change_password.html")

        if new_password != confirm_password:
            flash("Xác nhận mật khẩu mới không trùng khớp.", "danger")
            return render_template("admin/change_password.html")

        current_user.set_password(new_password)
        db.session.commit()
        flash("Đổi mật khẩu Admin thành công!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/change_password.html")


# ==========================================
# LEVEL MANAGEMENT (CRUD)
# ==========================================
@admin_bp.route("/levels", methods=["GET", "POST"])
@admin_required
def levels():
    """List & Create Levels."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        rank_order = request.form.get("rank_order", type=int)
        description = request.form.get("description", "").strip()

        if not name or rank_order is None:
            flash("Tên Level và Độ khó (Rank order) là bắt buộc.", "danger")
            return redirect(url_for("admin.levels"))

        if Level.query.filter_by(name=name).first():
            flash(f"Level với tên '{name}' đã tồn tại.", "danger")
            return redirect(url_for("admin.levels"))

        if Level.query.filter_by(rank_order=rank_order).first():
            flash(f"Độ khó rank_order = {rank_order} đã tồn tại.", "danger")
            return redirect(url_for("admin.levels"))

        level = Level(name=name, rank_order=rank_order, description=description)
        db.session.add(level)
        db.session.commit()
        flash(f"Thêm Level '{name}' thành công!", "success")
        return redirect(url_for("admin.levels"))

    all_levels = Level.query.order_by(Level.rank_order).all()
    return render_template("admin/levels.html", levels=all_levels)


@admin_bp.route("/levels/<int:level_id>/edit", methods=["POST"])
@admin_required
def edit_level(level_id):
    """Edit Level."""
    level = Level.query.get_or_404(level_id)
    name = request.form.get("name", "").strip()
    rank_order = request.form.get("rank_order", type=int)
    description = request.form.get("description", "").strip()

    if not name or rank_order is None:
        flash("Tên Level và Rank order không được để trống.", "danger")
        return redirect(url_for("admin.levels"))

    existing_name = Level.query.filter(Level.name == name, Level.id != level.id).first()
    if existing_name:
        flash(f"Tên Level '{name}' đã trùng với Level khác.", "danger")
        return redirect(url_for("admin.levels"))

    existing_rank = Level.query.filter(Level.rank_order == rank_order, Level.id != level.id).first()
    if existing_rank:
        flash(f"Rank order {rank_order} đã trùng với Level khác.", "danger")
        return redirect(url_for("admin.levels"))

    level.name = name
    level.rank_order = rank_order
    level.description = description
    db.session.commit()
    flash(f"Cập nhật Level '{name}' thành công!", "success")
    return redirect(url_for("admin.levels"))


@admin_bp.route("/levels/<int:level_id>/delete", methods=["POST"])
@admin_required
def delete_level(level_id):
    """Delete Level (checks if questions exist first)."""
    level = Level.query.get_or_404(level_id)
    question_count = Question.query.filter_by(level_id=level.id).count()
    if question_count > 0:
        flash(f"Không thể xóa Level '{level.name}' vì đang có {question_count} câu hỏi liên kết.", "danger")
        return redirect(url_for("admin.levels"))

    db.session.delete(level)
    db.session.commit()
    flash(f"Đã xóa Level '{level.name}'.", "info")
    return redirect(url_for("admin.levels"))


# ==========================================
# CATEGORY MANAGEMENT (2-tier CRUD)
# ==========================================
@admin_bp.route("/categories", methods=["GET", "POST"])
@admin_required
def categories():
    """List & Create Categories (supports 1-tier and 2-tier)."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        parent_id = request.form.get("parent_id", type=int)
        description = request.form.get("description", "").strip()

        if not name:
            flash("Tên chủ đề không được để trống.", "danger")
            return redirect(url_for("admin.categories"))

        category = Category(
            name=name,
            parent_id=parent_id if parent_id and parent_id > 0 else None,
            description=description
        )
        db.session.add(category)
        db.session.commit()
        flash(f"Đã thêm chủ đề '{name}' thành công!", "success")
        return redirect(url_for("admin.categories"))

    # Parent categories (level 1)
    parent_categories = Category.query.filter_by(parent_id=None).order_by(Category.name).all()
    all_categories = Category.query.order_by(Category.parent_id.desc(), Category.name).all()
    return render_template(
        "admin/categories.html",
        parent_categories=parent_categories,
        all_categories=all_categories
    )


@admin_bp.route("/categories/<int:category_id>/edit", methods=["POST"])
@admin_required
def edit_category(category_id):
    """Edit Category."""
    cat = Category.query.get_or_404(category_id)
    name = request.form.get("name", "").strip()
    parent_id = request.form.get("parent_id", type=int)
    description = request.form.get("description", "").strip()

    if not name:
        flash("Tên chủ đề không được để trống.", "danger")
        return redirect(url_for("admin.categories"))

    # Prevent circular reference: cannot set self as parent
    if parent_id == cat.id:
        flash("Chủ đề không thể tự nhận chính nó làm chủ đề cha.", "danger")
        return redirect(url_for("admin.categories"))

    cat.name = name
    cat.parent_id = parent_id if parent_id and parent_id > 0 else None
    cat.description = description
    db.session.commit()
    flash(f"Đã cập nhật chủ đề '{name}' thành công!", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@admin_required
def delete_category(category_id):
    """Delete Category."""
    cat = Category.query.get_or_404(category_id)
    name = cat.name
    db.session.delete(cat)
    db.session.commit()
    flash(f"Đã xóa chủ đề '{name}' và các chủ đề con liên quan.", "info")
    return redirect(url_for("admin.categories"))


# ==========================================
# QUESTION MANAGEMENT (Rich Text & CRUD)
# ==========================================
@admin_bp.route("/questions")
@admin_required
def questions():
    """List questions with search, category/level filters and pagination."""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    level_id = request.args.get("level_id", type=int)
    category_id = request.args.get("category_id", type=int)

    query = Question.query.join(Level, Question.level_id == Level.id)

    if search:
        query = query.filter(
            or_(
                Question.content.ilike(f"%{search}%"),
                Question.explanation.ilike(f"%{search}%"),
                Question.option_1.ilike(f"%{search}%"),
                Question.option_2.ilike(f"%{search}%")
            )
        )

    if level_id:
        query = query.filter(Question.level_id == level_id)

    if category_id:
        if category_id == -1:  # Filter general questions
            query = query.filter(Question.category_id.is_(None))
        else:
            # If parent category, include its children
            sub_ids = [c.id for c in Category.query.filter_by(parent_id=category_id).all()]
            query = query.filter(Question.category_id.in_([category_id] + sub_ids))

    pagination = query.order_by(desc(Question.id)).paginate(page=page, per_page=15, error_out=False)
    levels = Level.query.order_by(Level.rank_order).all()
    categories = Category.query.order_by(Category.name).all()

    return render_template(
        "admin/questions.html",
        pagination=pagination,
        levels=levels,
        categories=categories,
        search=search,
        selected_level_id=level_id,
        selected_category_id=category_id
    )


@admin_bp.route("/questions/create", methods=["GET", "POST"])
@admin_required
def create_question():
    """Create a new question with Rich Text Editor."""
    levels = Level.query.order_by(Level.rank_order).all()
    categories = Category.query.order_by(Category.name).all()

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        option_1 = request.form.get("option_1", "").strip()
        option_2 = request.form.get("option_2", "").strip()
        option_3 = request.form.get("option_3", "").strip()
        option_4 = request.form.get("option_4", "").strip()
        correct_option = request.form.get("correct_option", type=int)
        explanation = request.form.get("explanation", "").strip()
        level_id = request.form.get("level_id", type=int)
        category_id = request.form.get("category_id", type=int)

        if not content or not option_1 or not option_2 or not option_3 or not option_4:
            flash("Vui lòng điền nội dung câu hỏi và đầy đủ 4 lựa chọn.", "danger")
            return render_template("admin/question_form.html", levels=levels, categories=categories, question=None)

        if correct_option not in (1, 2, 3, 4):
            flash("Vui lòng chọn đáp án đúng (từ 1 đến 4).", "danger")
            return render_template("admin/question_form.html", levels=levels, categories=categories, question=None)

        if not level_id:
            flash("Vui lòng chọn Level cho câu hỏi.", "danger")
            return render_template("admin/question_form.html", levels=levels, categories=categories, question=None)

        question = Question(
            content=content,
            option_1=option_1,
            option_2=option_2,
            option_3=option_3,
            option_4=option_4,
            correct_option=correct_option,
            explanation=explanation,
            level_id=level_id,
            category_id=category_id if category_id and category_id > 0 else None
        )
        db.session.add(question)
        db.session.commit()
        flash("Đã thêm câu hỏi mới thành công!", "success")
        return redirect(url_for("admin.questions"))

    return render_template("admin/question_form.html", levels=levels, categories=categories, question=None)


@admin_bp.route("/questions/<int:question_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_question(question_id):
    """Edit question with Rich Text Editor."""
    question = Question.query.get_or_404(question_id)
    levels = Level.query.order_by(Level.rank_order).all()
    categories = Category.query.order_by(Category.name).all()

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        option_1 = request.form.get("option_1", "").strip()
        option_2 = request.form.get("option_2", "").strip()
        option_3 = request.form.get("option_3", "").strip()
        option_4 = request.form.get("option_4", "").strip()
        correct_option = request.form.get("correct_option", type=int)
        explanation = request.form.get("explanation", "").strip()
        level_id = request.form.get("level_id", type=int)
        category_id = request.form.get("category_id", type=int)

        if not content or not option_1 or not option_2 or not option_3 or not option_4:
            flash("Vui lòng điền nội dung câu hỏi và đầy đủ 4 lựa chọn.", "danger")
            return render_template("admin/question_form.html", levels=levels, categories=categories, question=question)

        if correct_option not in (1, 2, 3, 4):
            flash("Vui lòng chọn đáp án đúng (từ 1 đến 4).", "danger")
            return render_template("admin/question_form.html", levels=levels, categories=categories, question=question)

        question.content = content
        question.option_1 = option_1
        question.option_2 = option_2
        question.option_3 = option_3
        question.option_4 = option_4
        question.correct_option = correct_option
        question.explanation = explanation
        question.level_id = level_id
        question.category_id = category_id if category_id and category_id > 0 else None

        db.session.commit()
        flash(f"Đã cập nhật câu hỏi #{question.id} thành công!", "success")
        return redirect(url_for("admin.questions"))

    return render_template("admin/question_form.html", levels=levels, categories=categories, question=question)


@admin_bp.route("/questions/<int:question_id>/delete", methods=["POST"])
@admin_required
def delete_question(question_id):
    """Delete Question."""
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash(f"Đã xóa câu hỏi #{question_id} thành công.", "info")
    return redirect(url_for("admin.questions"))


# ==========================================
# EXCEL IMPORT & TEMPLATE DOWNLOAD
# ==========================================
@admin_bp.route("/questions/template")
@admin_required
def download_template():
    """Download pre-formatted Question Import Excel Template."""
    template_buffer = generate_excel_template()
    return send_file(
        template_buffer,
        as_attachment=True,
        download_name="EnglishPractice_Question_Template.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@admin_bp.route("/questions/import", methods=["GET", "POST"])
@admin_required
def import_excel():
    """Upload and batch import questions from Excel."""
    if request.method == "POST":
        file = request.files.get("excel_file")
        if not file or not file.filename:
            flash("Vui lòng chọn file Excel (.xlsx) để tải lên.", "warning")
            return render_template("admin/excel_import.html")

        if not file.filename.lower().endswith((".xlsx", ".xlsm")):
            flash("Chỉ chấp nhận file định dạng Excel (.xlsx).", "danger")
            return render_template("admin/excel_import.html")

        count, errors = import_questions_from_excel(file.stream)

        if errors:
            flash(f"Có {len(errors)} lỗi phát hiện trong file. Dữ liệu chưa được import:", "danger")
            return render_template("admin/excel_import.html", errors=errors)

        flash(f"Tuyệt vời! Đã import thành công {count} câu hỏi vào hệ thống.", "success")
        return redirect(url_for("admin.questions"))

    return render_template("admin/excel_import.html", errors=None)
