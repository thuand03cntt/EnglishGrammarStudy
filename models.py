from datetime import datetime, timezone, timedelta
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Level(db.Model):
    """Level of English proficiency (1: Beginner to 5: Advance)."""
    __tablename__ = "levels"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True, index=True)
    rank_order = db.Column(db.Integer, nullable=False, unique=True, index=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    users = db.relationship("User", back_populates="level")
    questions = db.relationship("Question", back_populates="level")

    def __repr__(self):
        return f"<Level {self.name} (Rank: {self.rank_order})>"


class User(UserMixin, db.Model):
    """User account: Candidate or single Admin."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(60), nullable=False, unique=True, index=True)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.String(10), default="Khác")  # Nam, Nữ, Khác
    avatar = db.Column(db.String(255), default="default_avatar.png")
    level_id = db.Column(db.Integer, db.ForeignKey("levels.id", ondelete="SET NULL"), nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Password reset fields
    reset_token = db.Column(db.String(100), nullable=True, unique=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    level = db.relationship("Level", back_populates="users")
    attempts = db.relationship("ExamAttempt", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self, expires_in_minutes: int = 30) -> str:
        """Generates a secure random token for password reset."""
        token = secrets.token_urlsafe(32)
        self.reset_token = token
        self.reset_token_expiry = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        return token

    def verify_reset_token(self, token: str) -> bool:
        """Validates if token matches and has not expired."""
        if not self.reset_token or self.reset_token != token:
            return False
        if not self.reset_token_expiry:
            return False
        expiry = self.reset_token_expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) <= expiry

    def clear_reset_token(self) -> None:
        self.reset_token = None
        self.reset_token_expiry = None

    @property
    def total_correct_answers(self) -> int:
        """Total correct answers accumulated across all completed attempts."""
        total = db.session.query(db.func.sum(ExamAttempt.correct_count))\
            .filter(ExamAttempt.user_id == self.id, ExamAttempt.completed_at.isnot(None))\
            .scalar()
        return int(total or 0)

    @property
    def total_exams_taken(self) -> int:
        """Total completed exams."""
        return self.attempts.filter(ExamAttempt.completed_at.isnot(None)).count()

    def __repr__(self):
        return f"<User {self.username} (Admin: {self.is_admin})>"


class Category(db.Model):
    """Two-tier Category hierarchy for Practice Topics (e.g. TOEIC -> Part 5)."""
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="CASCADE"), nullable=True, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    parent = db.relationship("Category", remote_side=[id], backref=db.backref("children", cascade="all, delete-orphan", lazy="joined"))
    questions = db.relationship("Question", back_populates="category", cascade="all, delete-orphan")
    attempts = db.relationship("ExamAttempt", back_populates="category")

    @property
    def is_parent(self) -> bool:
        return self.parent_id is None

    @property
    def full_name(self) -> str:
        if self.parent:
            return f"{self.parent.name} » {self.name}"
        return self.name

    def __repr__(self):
        return f"<Category {self.full_name}>"


class Question(db.Model):
    """Grammar exam questions with 4 choices, rich text, and explanations."""
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)  # Supports HTML Rich Text
    option_1 = db.Column(db.Text, nullable=False)
    option_2 = db.Column(db.Text, nullable=False)
    option_3 = db.Column(db.Text, nullable=False)
    option_4 = db.Column(db.Text, nullable=False)
    correct_option = db.Column(db.SmallInteger, nullable=False)  # 1, 2, 3, or 4
    explanation = db.Column(db.Text, nullable=True)  # Rich text explanation in Vietnamese
    
    level_id = db.Column(db.Integer, db.ForeignKey("levels.id", ondelete="RESTRICT"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    level = db.relationship("Level", back_populates="questions", lazy="joined")
    category = db.relationship("Category", back_populates="questions", lazy="joined")
    attempt_details = db.relationship("ExamAttemptDetail", back_populates="question", cascade="all, delete-orphan")

    def get_option_text(self, option_num: int) -> str:
        return {
            1: self.option_1,
            2: self.option_2,
            3: self.option_3,
            4: self.option_4,
        }.get(option_num, "")

    @property
    def correct_option_text(self) -> str:
        return self.get_option_text(self.correct_option)

    def __repr__(self):
        return f"<Question #{self.id} Level: {self.level_id}>"


class ExamAttempt(db.Model):
    """Record of an exam session taken by a candidate."""
    __tablename__ = "exam_attempts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    attempt_number = db.Column(db.Integer, nullable=False, default=1)
    total_questions = db.Column(db.Integer, nullable=False, default=10)
    correct_count = db.Column(db.Integer, nullable=False, default=0)
    wrong_count = db.Column(db.Integer, nullable=False, default=0)
    score = db.Column(db.Numeric(5, 2), nullable=False, default=0.00)  # Scale 100
    duration_seconds = db.Column(db.Integer, nullable=False, default=0)  # in seconds
    
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship("User", back_populates="attempts")
    category = db.relationship("Category", back_populates="attempts", lazy="joined")
    details = db.relationship("ExamAttemptDetail", back_populates="attempt", cascade="all, delete-orphan",
                             order_by="ExamAttemptDetail.question_order")

    @property
    def formatted_duration(self) -> str:
        """Convert duration_seconds to mm:ss or hh:mm:ss."""
        sec = self.duration_seconds
        hours = sec // 3600
        minutes = (sec % 3600) // 60
        seconds = sec % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None

    def __repr__(self):
        return f"<ExamAttempt #{self.id} User: {self.user_id} Score: {self.score}>"


class ExamAttemptDetail(db.Model):
    """Question-level detail for an exam attempt."""
    __tablename__ = "exam_attempt_details"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_option = db.Column(db.SmallInteger, nullable=True)  # 1, 2, 3, 4 or None
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    question_order = db.Column(db.Integer, nullable=False, default=1)

    # Relationships
    attempt = db.relationship("ExamAttempt", back_populates="details")
    question = db.relationship("Question", back_populates="attempt_details", lazy="joined")

    def __repr__(self):
        return f"<Detail Attempt: {self.attempt_id} Q: {self.question_id} Correct: {self.is_correct}>"
