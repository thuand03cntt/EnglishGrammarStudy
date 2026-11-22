import os
import uuid
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Level
from services.mail_service import send_reset_password_email

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def allowed_file(filename: str) -> bool:
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "webp"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("exam.index"))

    levels = Level.query.order_by(Level.rank_order).all()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        gender = request.form.get("gender", "Khác")
        level_id = request.form.get("level_id", type=int)

        # Basic validations
        if not username or not email or not password:
            flash("Vui lòng điền đầy đủ các thông tin bắt buộc.", "danger")
            return render_template("auth/register.html", levels=levels)

        if username.lower() == "admin":
            flash("Tên người dùng 'admin' được bảo lưu cho hệ thống.", "danger")
            return render_template("auth/register.html", levels=levels)

        if len(password) < 6:
            flash("Mật khẩu phải có ít nhất 6 ký tự.", "danger")
            return render_template("auth/register.html", levels=levels)

        if password != confirm_password:
            flash("Xác nhận mật khẩu không trùng khớp.", "danger")
            return render_template("auth/register.html", levels=levels)

        # Check existing username or email
        if User.query.filter_by(username=username).first():
            flash("Tên đăng nhập này đã tồn tại. Vui lòng chọn tên khác.", "danger")
            return render_template("auth/register.html", levels=levels)

        if User.query.filter_by(email=email).first():
            flash("Địa chỉ email này đã được đăng ký tài khoản.", "danger")
            return render_template("auth/register.html", levels=levels)

        # Handle avatar upload
        avatar_filename = "default_avatar.png"
        file = request.files.get("avatar")
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
            upload_dir.mkdir(parents=True, exist_ok=True)
            save_path = upload_dir / unique_name
            file.save(save_path)
            avatar_filename = unique_name

        # Create user
        new_user = User(
            username=username,
            email=email,
            gender=gender if gender in ("Nam", "Nữ", "Khác") else "Khác",
            avatar=avatar_filename,
            level_id=level_id,
            is_admin=False
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash("Đăng ký tài khoản thành công! Chào mừng bạn đến với hệ thống.", "success")
        return redirect(url_for("exam.index"))

    return render_template("auth/register.html", levels=levels)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("exam.index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        if not identifier or not password:
            flash("Vui lòng nhập tên đăng nhập/email và mật khẩu.", "warning")
            return render_template("auth/login.html")

        # Find by username or email
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Xin chào {user.username}, bạn đã đăng nhập thành công!", "success")
            
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            
            if user.is_admin:
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("exam.index"))
        else:
            flash("Tên đăng nhập/email hoặc mật khẩu không chính xác.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Bạn đã đăng xuất khỏi hệ thống.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("exam.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            flash("Vui lòng nhập địa chỉ email của bạn.", "warning")
            return render_template("auth/forgot_password.html")

        user = User.query.filter_by(email=email).first()
        if user:
            token = user.generate_reset_token(expires_in_minutes=30)
            db.session.commit()
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            send_reset_password_email(user, reset_url)
            flash(
                "Đã gửi hướng dẫn đặt lại mật khẩu đến email của bạn. "
                "Nếu đang chạy chế độ phát triển (dev/local), vui lòng kiểm tra console terminal để lấy link reset.",
                "info"
            )
            return redirect(url_for("auth.login"))
        else:
            # For security, avoid revealing if email exists or not, but give clear hint
            flash("Nếu email tồn tại trong hệ thống, hướng dẫn đặt lại mật khẩu sẽ được gửi đến hộp thư.", "info")
            return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("exam.index"))

    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.verify_reset_token(token):
        flash("Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn (quá 30 phút).", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(password) < 6:
            flash("Mật khẩu mới phải có ít nhất 6 ký tự.", "danger")
            return render_template("auth/reset_password.html", token=token)

        if password != confirm_password:
            flash("Xác nhận mật khẩu không khớp.", "danger")
            return render_template("auth/reset_password.html", token=token)

        user.set_password(password)
        user.clear_reset_token()
        db.session.commit()

        flash("Đặt lại mật khẩu thành công! Bây giờ bạn có thể đăng nhập bằng mật khẩu mới.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    levels = Level.query.order_by(Level.rank_order).all()

    if request.method == "POST":
        gender = request.form.get("gender", current_user.gender)
        level_id = request.form.get("level_id", type=int)
        new_password = request.form.get("new_password", "").strip()

        # Update gender and level
        if gender in ("Nam", "Nữ", "Khác"):
            current_user.gender = gender
        if level_id:
            current_user.level_id = level_id

        # Update password if provided
        if new_password:
            if len(new_password) < 6:
                flash("Mật khẩu mới phải có ít nhất 6 ký tự.", "danger")
                return render_template("auth/profile.html", levels=levels)
            current_user.set_password(new_password)
            flash("Đã đổi mật khẩu thành công.", "success")

        # Handle avatar change
        file = request.files.get("avatar")
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
            upload_dir.mkdir(parents=True, exist_ok=True)
            file.save(upload_dir / unique_name)
            current_user.avatar = unique_name

        db.session.commit()
        flash("Thông tin hồ sơ cá nhân đã được cập nhật thành công!", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", levels=levels)
