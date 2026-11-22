"""
services/seed_data.py
Module to seed all initial default data for EnglishPractice:
- 5 Levels (Beginner -> Advance)
- Single Admin user (admin / 123456a@)
- Sample candidate users for leaderboard (mai_anh, hoang_nam, quoc_viet)
- 2-tier Category tree (TOEIC, TOEFL, Bằng A/B/C, Tenses)
- 30 rich-text English Grammar questions with detailed Vietnamese explanations
- Sample exam attempts for demonstration
"""

from datetime import datetime, timezone, timedelta
from models import db, Level, User, Category, Question, ExamAttempt, ExamAttemptDetail

def seed_all_initial_data():
    """
    Seeds all required initial system data into the database if missing.
    Ensures that categories and 30 sample questions are ALWAYS present.
    """
    # 1. Seed 5 Levels
    default_levels = [
        {"id": 1, "name": "Beginner", "rank_order": 1, "description": "Người mới bắt đầu: nhận biết các thì cơ bản, từ vựng và câu đơn giản."},
        {"id": 2, "name": "Elementary", "rank_order": 2, "description": "Sơ cấp: so sánh, quá khứ đơn, lượng từ và câu ghép căn bản."},
        {"id": 3, "name": "Pre-intermediate", "rank_order": 3, "description": "Tiền trung cấp: thì hoàn thành, mệnh đề quan hệ và câu điều kiện 1."},
        {"id": 4, "name": "Intermediate", "rank_order": 4, "description": "Trung cấp: thể bị động nâng cao, câu điều kiện 2 & 3, câu phức."},
        {"id": 5, "name": "Advance", "rank_order": 5, "description": "Nâng cao: đảo ngữ, thể giả định, rút gọn mệnh đề và cấu trúc học thuật."}
    ]

    for lvl_data in default_levels:
        lvl = Level.query.filter_by(name=lvl_data["name"]).first()
        if not lvl:
            new_lvl = Level(
                name=lvl_data["name"],
                rank_order=lvl_data["rank_order"],
                description=lvl_data["description"]
            )
            db.session.add(new_lvl)
    db.session.commit()

    # Re-cache levels
    level_map = {lvl.name: lvl.id for lvl in Level.query.all()}

    # 2. Seed Single Admin
    admin_user = User.query.filter_by(username="admin").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@englishpractice.local",
            gender="Nam",
            avatar="default_avatar.png",
            level_id=level_map.get("Advance", 5),
            is_admin=True
        )
        admin_user.set_password("123456a@")
        db.session.add(admin_user)

    # 3. Seed Sample Candidate Users
    sample_users = [
        {"username": "mai_anh", "email": "maianh.le@example.com", "gender": "Nữ", "level_name": "Intermediate"},
        {"username": "hoang_nam", "email": "nam.nguyen@example.com", "gender": "Nam", "level_name": "Elementary"},
        {"username": "quoc_viet", "email": "viet.tran@example.com", "gender": "Nam", "level_name": "Pre-intermediate"}
    ]
    for u in sample_users:
        if not User.query.filter_by(username=u["username"]).first():
            user_obj = User(
                username=u["username"],
                email=u["email"],
                gender=u["gender"],
                avatar="default_avatar.png",
                level_id=level_map.get(u["level_name"], 1),
                is_admin=False
            )
            user_obj.set_password("123456a@")
            db.session.add(user_obj)
    db.session.commit()

    # 4. Seed 2-tier Category Tree
    # 4.1 Parent Categories (Cấp 1)
    parents_data = [
        {"name": "Luyện thi TOEIC", "description": "Các dạng bài thi chuẩn hóa TOEIC Reading & Listening"},
        {"name": "Luyện thi TOEFL", "description": "Ngữ pháp học thuật và cấu trúc câu cho kỳ thi TOEFL iBT/ITP"},
        {"name": "Tiếng Anh Chứng chỉ A, B, C", "description": "Chương trình chứng chỉ quốc gia A, B, C theo khung chuẩn"},
        {"name": "Thì & Cấu trúc câu Tổng quát", "description": "Hệ thống 12 thì và quy tắc ngữ pháp căn bản đến nâng cao"}
    ]

    for p in parents_data:
        cat = Category.query.filter_by(name=p["name"], parent_id=None).first()
        if not cat:
            db.session.add(Category(name=p["name"], parent_id=None, description=p["description"]))
    db.session.commit()

    # Map parent names to IDs
    parent_cat_map = {c.name: c.id for c in Category.query.filter_by(parent_id=None).all()}

    # 4.2 Subcategories (Cấp 2)
    subcategories_data = [
        # Children of TOEIC
        {"name": "Part 5 - Hoàn thành câu (Incomplete Sentences)", "parent_name": "Luyện thi TOEIC", "description": "Kiểm tra từ vựng và ngữ pháp trọng tâm TOEIC Part 5"},
        {"name": "Part 6 - Hoàn thành đoạn văn (Text Completion)", "parent_name": "Luyện thi TOEIC", "description": "Điền từ và ngữ pháp theo ngữ cảnh đoạn văn TOEIC"},
        # Children of TOEFL
        {"name": "Sentence Structure & Grammar", "parent_name": "Luyện thi TOEFL", "description": "Nhận diện cấu trúc mệnh đề chính, phụ và cụm từ TOEFL"},
        {"name": "Written Expression & Error Identification", "parent_name": "Luyện thi TOEFL", "description": "Tìm lỗi sai ngữ pháp trong bài thi học thuật TOEFL"},
        # Children of Chứng chỉ A, B, C
        {"name": "Chứng chỉ A - Căn bản", "parent_name": "Tiếng Anh Chứng chỉ A, B, C", "description": "Ngữ pháp vỡ lòng và giao tiếp sơ cấp"},
        {"name": "Chứng chỉ B - Trung cấp", "parent_name": "Tiếng Anh Chứng chỉ A, B, C", "description": "Ngữ pháp trung cấp và kỹ năng viết thư, đoạn văn"},
        {"name": "Chứng chỉ C - Nâng cao", "parent_name": "Tiếng Anh Chứng chỉ A, B, C", "description": "Ngữ pháp phức tạp và thuật ngữ tiếng Anh chuyên ngành"}
    ]

    for sub in subcategories_data:
        p_id = parent_cat_map.get(sub["parent_name"])
        if p_id:
            existing_sub = Category.query.filter_by(name=sub["name"], parent_id=p_id).first()
            if not existing_sub:
                db.session.add(Category(name=sub["name"], parent_id=p_id, description=sub["description"]))
    db.session.commit()

    # Build full category lookup for questions
    all_cats = {c.name: c.id for c in Category.query.all()}

    # 5. Seed 30 Questions if DB has fewer than 10 questions
    current_question_count = Question.query.count()
    if current_question_count < 10:
        questions_data = [
            # --- BEGINNER (Rank 1) ---
            {
                "content": "<p>My sister usually <strong>______</strong> up at 6:00 AM every weekday to prepare for work.</p>",
                "option_1": "wake", "option_2": "wakes", "option_3": "waking", "option_4": "is waking",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> Trạng từ tần suất <em>usually</em> và cụm <em>every weekday</em> là dấu hiệu của <strong>Thì Hiện tại đơn</strong> diễn tả thói quen lặp đi lặp lại. Chủ ngữ <em>My sister</em> (ngôi thứ 3 số ít) đi với động từ thêm <strong>-s</strong> (<em>wakes</em>).</p>",
                "level_name": "Beginner", "cat_name": "Thì & Cấu trúc câu Tổng quát"
            },
            {
                "content": "<p>Could you please pass me <strong>______</strong> apple on the fruit basket?</p>",
                "option_1": "a", "option_2": "an", "option_3": "the", "option_4": "some",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> Danh từ <em>apple</em> bắt đầu bằng một nguyên âm (/ˈæp.əl/), vì vậy khi ở dạng số ít đếm được chưa xác định ta sử dụng mạo từ <strong>an</strong>.</p>",
                "level_name": "Beginner", "cat_name": "Chứng chỉ A - Căn bản"
            },
            {
                "content": "<p>The international seminar will officially start <strong>______</strong> 9:00 AM on Monday morning.</p>",
                "option_1": "at", "option_2": "in", "option_3": "on", "option_4": "by",
                "correct_option": 1,
                "explanation": "<p><strong>Giải thích:</strong> Quy tắc giới từ thời gian: dùng <strong>at</strong> trước mốc giờ cụ thể trong ngày (<em>at 9:00 AM</em>), dùng <em>on</em> trước thứ/ngày, và <em>in</em> trước tháng/năm/mùa.</p>",
                "level_name": "Beginner", "cat_name": "Part 5 - Hoàn thành câu (Incomplete Sentences)"
            },
            {
                "content": "<p>This is my new laptop. Where did you put <strong>______</strong>?</p>",
                "option_1": "your", "option_2": "yours", "option_3": "it", "option_4": "its",
                "correct_option": 3,
                "explanation": "<p><strong>Giải thích:</strong> Đại từ tân ngữ <strong>it</strong> thay thế cho danh từ chỉ đồ vật số ít đã được đề cập trước đó (<em>my new laptop</em>).</p>",
                "level_name": "Beginner", "cat_name": None  # Câu dùng chung
            },
            {
                "content": "<p>Listen! The children <strong>______</strong> quietly in their bedroom upstairs.</p>",
                "option_1": "sleep", "option_2": "are sleeping", "option_3": "slept", "option_4": "have slept",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> Lời kêu gọi chú ý <em>Listen!</em> báo hiệu hành động đang diễn ra tại thời điểm nói -> Dùng <strong>Thì Hiện tại tiếp diễn</strong>: <em>are sleeping</em>.</p>",
                "level_name": "Beginner", "cat_name": "Thì & Cấu trúc câu Tổng quát"
            },
            {
                "content": "<p>How <strong>______</strong> glasses of water do you drink on a daily basis?</p>",
                "option_1": "much", "option_2": "many", "option_3": "long", "option_4": "often",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> <em>glasses of water</em> là cụm danh từ đếm được số nhiều -> Dùng <strong>How many</strong> để hỏi số lượng (dùng <em>How much</em> cho danh từ không đếm được).</p>",
                "level_name": "Beginner", "cat_name": "Chứng chỉ A - Căn bản"
            },

            # --- ELEMENTARY (Rank 2) ---
            {
                "content": "<p>Last night, our family <strong>______</strong> an extraordinary movie at the cinema.</p>",
                "option_1": "watch", "option_2": "watches", "option_3": "watched", "option_4": "watching",
                "correct_option": 3,
                "explanation": "<p><strong>Giải thích:</strong> Dấu hiệu <em>Last night</em> (tối qua) chỉ thời điểm đã kết thúc trong quá khứ -> Dùng <strong>Thì Quá khứ đơn</strong>: <em>watched</em>.</p>",
                "level_name": "Elementary", "cat_name": "Thì & Cấu trúc câu Tổng quát"
            },
            {
                "content": "<p>Mount Everest is significantly <strong>______</strong> than any other mountain on Earth.</p>",
                "option_1": "high", "option_2": "higher", "option_3": "highest", "option_4": "more high",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> Cấu trúc <strong>so sánh hơn</strong> của tính từ ngắn (1 âm tiết): <em>adj-er + than</em>. Tính từ <em>high</em> trở thành <strong>higher</strong>.</p>",
                "level_name": "Elementary", "cat_name": "Sentence Structure & Grammar"
            },
            {
                "content": "<p>You haven't completed the quarterly financial report yet, <strong>______</strong>?</p>",
                "option_1": "haven't you", "option_2": "have you", "option_3": "do you", "option_4": "did you",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> <strong>Câu hỏi đuôi (Tag question)</strong>: Mệnh đề chính ở thể phủ định (<em>haven't completed</em>) thì câu hỏi đuôi ở thể khẳng định: <strong>have you</strong>.</p>",
                "level_name": "Elementary", "cat_name": "Part 5 - Hoàn thành câu (Incomplete Sentences)"
            },
            {
                "content": "<p>Due to the sudden rainstorm, we decided to stay <strong>______</strong> home.</p>",
                "option_1": "in", "option_2": "on", "option_3": "at", "option_4": "with",
                "correct_option": 3,
                "explanation": "<p><strong>Giải thích:</strong> Cụm cố định chỉ nơi chốn: <strong>at home</strong> (ở nhà), tương tự như <em>at school, at work</em>.</p>",
                "level_name": "Elementary", "cat_name": None  # Câu dùng chung
            },
            {
                "content": "<p>Passengers <strong>______</strong> fasten their seat belts securely during takeoff and landing.</p>",
                "option_1": "must", "option_2": "can", "option_3": "may", "option_4": "might",
                "correct_option": 1,
                "explanation": "<p><strong>Giải thích:</strong> Động từ khuyết thiếu <strong>must</strong> diễn tả quy định bắt buộc, mệnh lệnh an toàn bắt buộc trên chuyến bay.</p>",
                "level_name": "Elementary", "cat_name": "Part 5 - Hoàn thành câu (Incomplete Sentences)"
            },
            {
                "content": "<p>She bought a <strong>______</strong> car after receiving her year-end promotion.</p>",
                "option_1": "new red Japanese", "option_2": "Japanese new red", "option_3": "red new Japanese", "option_4": "new Japanese red",
                "correct_option": 1,
                "explanation": "<p><strong>Giải thích:</strong> Quy tắc trật tự tính từ <strong>OSASCOMP</strong>: Age (<em>new</em>) -> Color (<em>red</em>) -> Origin (<em>Japanese</em>): <em>new red Japanese</em>.</p>",
                "level_name": "Elementary", "cat_name": "Chứng chỉ B - Trung cấp"
            },

            # --- PRE-INTERMEDIATE (Rank 3) ---
            {
                "content": "<p>Mr. Jonathan has worked as a senior software consultant for this enterprise <strong>______</strong> 2018.</p>",
                "option_1": "for", "option_2": "since", "option_3": "in", "option_4": "during",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> Trong <strong>Thì Hiện tại hoàn thành</strong>, dùng <strong>since</strong> trước mốc thời gian cụ thể (<em>since 2018</em>), dùng <em>for</em> trước khoảng thời gian.</p>",
                "level_name": "Pre-intermediate", "cat_name": "Part 5 - Hoàn thành câu (Incomplete Sentences)"
            },
            {
                "content": "<p>If it <strong>______</strong> sunny tomorrow afternoon, we will host an outdoor barbecue party.</p>",
                "option_1": "is", "option_2": "will be", "option_3": "was", "option_4": "were",
                "correct_option": 1,
                "explanation": "<p><strong>Giải thích:</strong> <strong>Câu điều kiện loại 1</strong>: Mệnh đề <em>If</em> chia Hiện tại đơn (<em>is</em>), mệnh đề chính dùng <em>will + V-bare</em>.</p>",
                "level_name": "Pre-intermediate", "cat_name": "Thì & Cấu trúc câu Tổng quát"
            },
            {
                "content": "<p>The experienced engineer <strong>______</strong> repaired our main assembly line was praised by the director.</p>",
                "option_1": "which", "option_2": "who", "option_3": "whom", "option_4": "whose",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> Đại từ quan hệ <strong>who</strong> thay thế cho danh từ chỉ người (<em>The experienced engineer</em>) làm chủ ngữ trong mệnh đề quan hệ.</p>",
                "level_name": "Pre-intermediate", "cat_name": "Sentence Structure & Grammar"
            },
            {
                "content": "<p>The marketing manager strongly suggested <strong>______</strong> a consumer survey before launching the campaign.</p>",
                "option_1": "conduct", "option_2": "to conduct", "option_3": "conducting", "option_4": "conducted",
                "correct_option": 3,
                "explanation": "<p><strong>Giải thích:</strong> Cấu trúc: <em>suggest + V-ing</em> (đề xuất làm việc gì) -> chọn <strong>conducting</strong>.</p>",
                "level_name": "Pre-intermediate", "cat_name": "Part 5 - Hoàn thành câu (Incomplete Sentences)"
            },
            {
                "content": "<p>The iconic Sydney Opera House <strong>______</strong> by Danish architect Jørn Utzon in the mid-20th century.</p>",
                "option_1": "designed", "option_2": "was designed", "option_3": "is designed", "option_4": "has been designed",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> Câu bị động ở Thì Quá khứ đơn: <strong>was/were + V3/V-ed</strong>. Chủ ngữ số ít nên dùng <em>was designed</em>.</p>",
                "level_name": "Pre-intermediate", "cat_name": "Chứng chỉ B - Trung cấp"
            },
            {
                "content": "<p><strong>______</strong> the severe financial crisis, the innovative startup managed to turn a profit.</p>",
                "option_1": "Although", "option_2": "Even though", "option_3": "Despite", "option_4": "Because",
                "correct_option": 3,
                "explanation": "<p><strong>Giải thích:</strong> <em>the severe financial crisis</em> là một cụm danh từ (Noun phrase) -> Dùng <strong>Despite</strong> / <em>In spite of</em> để diễn đạt sự nhượng bộ (<em>Although/Even though</em> đi với mệnh đề S+V).</p>",
                "level_name": "Pre-intermediate", "cat_name": "Part 6 - Hoàn thành đoạn văn (Text Completion)"
            },

            # --- INTERMEDIATE (Rank 4) ---
            {
                "content": "<p>If I <strong>______</strong> enough capital right now, I would invest heavily in green renewable energy.</p>",
                "option_1": "have", "option_2": "had", "option_3": "have had", "option_4": "would have",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> <strong>Câu điều kiện loại 2</strong> giả định trái ngược với hiện tại: <em>If + S + V2/V-ed</em> (chọn <strong>had</strong>), mệnh đề chính <em>would + V</em>.</p>",
                "level_name": "Intermediate", "cat_name": "Thì & Cấu trúc câu Tổng quát"
            },
            {
                "content": "<p>The prominent pharmaceutical company, <strong>______</strong> headquarters is located in Basel, announced a medical breakthrough.</p>",
                "option_1": "which", "option_2": "whose", "option_3": "where", "option_4": "that",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> Đại từ sở hữu <strong>whose</strong> đứng giữa hai danh từ chỉ mối quan hệ thuộc quyền sở hữu (trụ sở của công ty).</p>",
                "level_name": "Intermediate", "cat_name": "Written Expression & Error Identification"
            },
            {
                "content": "<p>By the time the rescue team arrived at the hazardous site, the trapped miners <strong>______</strong> for over ten hours.</p>",
                "option_1": "waited", "option_2": "have waited", "option_3": "had been waiting", "option_4": "are waiting",
                "correct_option": 3,
                "explanation": "<p><strong>Giải thích:</strong> Cấu trúc <em>By the time + S + V-past</em>: hành động đợi đã diễn ra liên tục trước đó trong quá khứ -> Dùng <strong>Thì Quá khứ hoàn thành tiếp diễn (had been waiting)</strong>.</p>",
                "level_name": "Intermediate", "cat_name": "Sentence Structure & Grammar"
            },
            {
                "content": "<p>He looked utterly exhausted after the exam. He <strong>______</strong> burning the midnight oil for weeks.</p>",
                "option_1": "must have been", "option_2": "can't have been", "option_3": "should have been", "option_4": "needn't have been",
                "correct_option": 1,
                "explanation": "<p><strong>Giải thích:</strong> <strong>must have + V3/V-ed</strong>: suy đoán hợp lý và chắc chắn về một sự việc đã diễn ra trong quá khứ dựa trên bằng chứng rõ ràng.</p>",
                "level_name": "Intermediate", "cat_name": "Chứng chỉ C - Nâng cao"
            },
            {
                "content": "<p>Had the board members reviewed the contractual terms carefully, they <strong>______</strong> into such a dispute.</p>",
                "option_1": "would not enter", "option_2": "would not have entered", "option_3": "will not enter", "option_4": "had not entered",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> <strong>Đảo ngữ Câu điều kiện loại 3</strong>: <em>Had + S + V3/V-ed, S + would have + V3/V-ed</em>.</p>",
                "level_name": "Intermediate", "cat_name": "Part 5 - Hoàn thành câu (Incomplete Sentences)"
            },
            {
                "content": "<p>We take immense pride in <strong>______</strong> our quarterly sales targets despite unfavorable market conditions.</p>",
                "option_1": "achieve", "option_2": "achieved", "option_3": "having achieved", "option_4": "to achieve",
                "correct_option": 3,
                "explanation": "<p><strong>Giải thích:</strong> Sau giới từ <em>in</em> dùng phân từ hoàn thành <strong>having achieved</strong> để nhấn mạnh hành động đạt mục tiêu đã hoàn tất trước.</p>",
                "level_name": "Intermediate", "cat_name": None  # Câu dùng chung
            },

            # --- ADVANCE (Rank 5) ---
            {
                "content": "<p>Rarely <strong>______</strong> such breathtaking panoramic vistas during our mountaineering expedition.</p>",
                "option_1": "we encountered", "option_2": "did we encounter", "option_3": "have we encounter", "option_4": "we did encounter",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> <strong>Đảo ngữ với trạng từ phủ định</strong> đứng đầu câu: <em>Rarely + did + S + V-bare</em> -> <strong>did we encounter</strong>.</p>",
                "level_name": "Advance", "cat_name": "Sentence Structure & Grammar"
            },
            {
                "content": "<p>The government inspection committee demanded that the hazardous chemical plant <strong>______</strong> operations immediately.</p>",
                "option_1": "suspended", "option_2": "suspends", "option_3": "suspend", "option_4": "is suspending",
                "correct_option": 3,
                "explanation": "<p><strong>Giải thích:</strong> <strong>Thể giả định (Subjunctive Mood)</strong>: <em>demand that + S + (should) + V-bare</em> -> chọn <strong>suspend</strong> nguyên thể không chia.</p>",
                "level_name": "Advance", "cat_name": "Written Expression & Error Identification"
            },
            {
                "content": "<p><strong>______</strong> for the timely intervention of the paramedic, the patient might not have survived.</p>",
                "option_1": "Were it not", "option_2": "Had it not been", "option_3": "If it was not", "option_4": "Should it not be",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> Cấu trúc đảo ngữ điều kiện loại 3: <strong>Had it not been for + Noun phrase</strong> (Nếu không nhờ có...).</p>",
                "level_name": "Advance", "cat_name": "Chứng chỉ C - Nâng cao"
            },
            {
                "content": "<p><strong>______</strong> from the prestigious university with highest honors, Elena was immediately recruited by a Fortune 500 company.</p>",
                "option_1": "Graduating", "option_2": "Having graduated", "option_3": "Graduated", "option_4": "To graduate",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> Rút gọn mệnh đề phân từ hoàn thành: <strong>Having + V3/V-ed</strong> nhấn mạnh việc tốt nghiệp đã hoàn tất trọn vẹn trước khi được tuyển dụng.</p>",
                "level_name": "Advance", "cat_name": "Part 6 - Hoàn thành đoạn văn (Text Completion)"
            },
            {
                "content": "<p>No sooner had the keynote speaker stepped onto the stage <strong>______</strong> the auditorium erupted in thunderous applause.</p>",
                "option_1": "when", "option_2": "than", "option_3": "then", "option_4": "hardly",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> Cặp liên từ đảo ngữ: <strong>No sooner ... THAN</strong> (Ngay khi... thì...).</p>",
                "level_name": "Advance", "cat_name": "Written Expression & Error Identification"
            },
            {
                "content": "<p>It was not until midnight <strong>______</strong> the weary travelers finally arrived at their remote destination.</p>",
                "option_1": "when", "option_2": "that", "option_3": "which", "option_4": "than",
                "correct_option": 2,
                "explanation": "<p><strong>Giải thích:</strong> Cấu trúc câu chẻ (Cleft sentence) nhấn mạnh: <strong>It was not until ... THAT + S + V</strong>.</p>",
                "level_name": "Advance", "cat_name": "Chứng chỉ C - Nâng cao"
            }
        ]

        for q in questions_data:
            lvl_id = level_map.get(q["level_name"], 1)
            cat_id = all_cats.get(q["cat_name"]) if q["cat_name"] else None
            new_q = Question(
                content=q["content"],
                option_1=q["option_1"],
                option_2=q["option_2"],
                option_3=q["option_3"],
                option_4=q["option_4"],
                correct_option=q["correct_option"],
                explanation=q["explanation"],
                level_id=lvl_id,
                category_id=cat_id
            )
            db.session.add(new_q)
        db.session.commit()
        print(f"Successfully seeded {len(questions_data)} sample questions.")

    # 6. Seed Sample Exam Attempts for Leaderboard if empty
    if ExamAttempt.query.count() == 0:
        mai_anh = User.query.filter_by(username="mai_anh").first()
        hoang_nam = User.query.filter_by(username="hoang_nam").first()
        quoc_viet = User.query.filter_by(username="quoc_viet").first()
        first_cat = Category.query.first()

        now = datetime.now(timezone.utc)
        if mai_anh:
            att1 = ExamAttempt(
                user_id=mai_anh.id,
                category_id=first_cat.id if first_cat else None,
                attempt_number=1,
                total_questions=10,
                correct_count=10,
                wrong_count=0,
                score=100.00,
                duration_seconds=245,
                started_at=now - timedelta(days=2),
                completed_at=now - timedelta(days=2)
            )
            db.session.add(att1)
            att2 = ExamAttempt(
                user_id=mai_anh.id,
                category_id=first_cat.id if first_cat else None,
                attempt_number=2,
                total_questions=10,
                correct_count=9,
                wrong_count=1,
                score=90.00,
                duration_seconds=310,
                started_at=now - timedelta(days=1),
                completed_at=now - timedelta(days=1)
            )
            db.session.add(att2)

        if hoang_nam:
            att3 = ExamAttempt(
                user_id=hoang_nam.id,
                category_id=first_cat.id if first_cat else None,
                attempt_number=1,
                total_questions=10,
                correct_count=8,
                wrong_count=2,
                score=80.00,
                duration_seconds=420,
                started_at=now - timedelta(days=3),
                completed_at=now - timedelta(days=3)
            )
            db.session.add(att3)

        if quoc_viet:
            att4 = ExamAttempt(
                user_id=quoc_viet.id,
                category_id=first_cat.id if first_cat else None,
                attempt_number=1,
                total_questions=10,
                correct_count=7,
                wrong_count=3,
                score=70.00,
                duration_seconds=510,
                started_at=now - timedelta(days=1),
                completed_at=now - timedelta(days=1)
            )
            db.session.add(att4)

        db.session.commit()
        print("Successfully seeded sample exam attempts for leaderboard.")
