-- ========================================================
-- EnglishPractice Database Initialization Dump (MariaDB 10.11+)
-- Character Set: utf8mb4, Collation: utf8mb4_unicode_ci
-- ========================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- --------------------------------------------------------
-- Table structure for levels
-- --------------------------------------------------------
DROP TABLE IF EXISTS `exam_attempt_details`;
DROP TABLE IF EXISTS `exam_attempts`;
DROP TABLE IF EXISTS `questions`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `levels`;

CREATE TABLE `levels` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL,
  `rank_order` INT NOT NULL,
  `description` VARCHAR(255) DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_levels_name` (`name`),
  UNIQUE KEY `uq_levels_rank_order` (`rank_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- Table structure for users
-- --------------------------------------------------------
CREATE TABLE `users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(60) NOT NULL,
  `email` VARCHAR(120) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `gender` VARCHAR(10) DEFAULT 'Khác',
  `avatar` VARCHAR(255) DEFAULT 'default_avatar.png',
  `level_id` INT DEFAULT NULL,
  `is_admin` TINYINT(1) NOT NULL DEFAULT 0,
  `reset_token` VARCHAR(100) DEFAULT NULL,
  `reset_token_expiry` DATETIME DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_username` (`username`),
  UNIQUE KEY `uq_users_email` (`email`),
  UNIQUE KEY `uq_users_reset_token` (`reset_token`),
  KEY `idx_users_level_id` (`level_id`),
  KEY `idx_users_is_admin` (`is_admin`),
  CONSTRAINT `fk_users_level` FOREIGN KEY (`level_id`) REFERENCES `levels` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- Table structure for categories (2-tier hierarchy)
-- --------------------------------------------------------
CREATE TABLE `categories` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(150) NOT NULL,
  `parent_id` INT DEFAULT NULL,
  `description` TEXT DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_categories_parent_id` (`parent_id`),
  CONSTRAINT `fk_categories_parent` FOREIGN KEY (`parent_id`) REFERENCES `categories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- Table structure for questions
-- --------------------------------------------------------
CREATE TABLE `questions` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `content` TEXT NOT NULL,
  `option_1` TEXT NOT NULL,
  `option_2` TEXT NOT NULL,
  `option_3` TEXT NOT NULL,
  `option_4` TEXT NOT NULL,
  `correct_option` TINYINT NOT NULL,
  `explanation` TEXT DEFAULT NULL,
  `level_id` INT NOT NULL,
  `category_id` INT DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_questions_level_id` (`level_id`),
  KEY `idx_questions_category_id` (`category_id`),
  CONSTRAINT `fk_questions_level` FOREIGN KEY (`level_id`) REFERENCES `levels` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_questions_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- Table structure for exam_attempts
-- --------------------------------------------------------
CREATE TABLE `exam_attempts` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `category_id` INT DEFAULT NULL,
  `attempt_number` INT NOT NULL DEFAULT 1,
  `total_questions` INT NOT NULL DEFAULT 10,
  `correct_count` INT NOT NULL DEFAULT 0,
  `wrong_count` INT NOT NULL DEFAULT 0,
  `score` DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  `duration_seconds` INT NOT NULL DEFAULT 0,
  `started_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `completed_at` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_attempts_user_id` (`user_id`),
  KEY `idx_attempts_category_id` (`category_id`),
  KEY `idx_attempts_completed_at` (`completed_at`),
  CONSTRAINT `fk_attempts_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_attempts_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- Table structure for exam_attempt_details
-- --------------------------------------------------------
CREATE TABLE `exam_attempt_details` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `attempt_id` INT NOT NULL,
  `question_id` INT NOT NULL,
  `selected_option` TINYINT DEFAULT NULL,
  `is_correct` TINYINT(1) NOT NULL DEFAULT 0,
  `question_order` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_details_attempt_id` (`attempt_id`),
  KEY `idx_details_question_id` (`question_id`),
  CONSTRAINT `fk_details_attempt` FOREIGN KEY (`attempt_id`) REFERENCES `exam_attempts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_details_question` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- ========================================================
-- SEED DATA: Levels (5 Proficiency Tiers)
-- ========================================================
INSERT INTO `levels` (`id`, `name`, `rank_order`, `description`, `created_at`) VALUES
(1, 'Beginner', 1, 'Trình độ khởi đầu: nhận biết các thì cơ bản, từ vựng và câu đơn giản.', NOW()),
(2, 'Elementary', 2, 'Trình độ sơ cấp: so sánh, quá khứ đơn, lượng từ và câu ghép căn bản.', NOW()),
(3, 'Pre-intermediate', 3, 'Trình độ tiền trung cấp: thì hoàn thành, mệnh đề quan hệ và câu điều kiện 1.', NOW()),
(4, 'Intermediate', 4, 'Trình độ trung cấp: thể bị động nâng cao, câu điều kiện 2 & 3, câu phức.', NOW()),
(5, 'Advance', 5, 'Trình độ nâng cao: đảo ngữ, thể giả định, rút gọn mệnh đề và cấu trúc học thuật.', NOW());

-- ========================================================
-- SEED DATA: Single Admin User & Sample Candidates
-- Default admin password: '123456a@'
-- ========================================================
INSERT INTO `users` (`id`, `username`, `email`, `password_hash`, `gender`, `avatar`, `level_id`, `is_admin`, `created_at`) VALUES
(1, 'admin', 'admin@englishpractice.local', 'pbkdf2:sha256:600000$772fbcb316ed0ab9$11177e390e333e27337721a1e8434796c23953cfdad01829f3aa0855130a44e5', 'Nam', 'default_avatar.png', 5, 1, NOW()),
(2, 'hoang_nam', 'nam.nguyen@example.com', 'pbkdf2:sha256:600000$772fbcb316ed0ab9$11177e390e333e27337721a1e8434796c23953cfdad01829f3aa0855130a44e5', 'Nam', 'default_avatar.png', 2, 0, NOW()),
(3, 'mai_anh', 'maianh.le@example.com', 'pbkdf2:sha256:600000$772fbcb316ed0ab9$11177e390e333e27337721a1e8434796c23953cfdad01829f3aa0855130a44e5', 'Nữ', 'default_avatar.png', 4, 0, NOW()),
(4, 'quoc_viet', 'viet.tran@example.com', 'pbkdf2:sha256:600000$772fbcb316ed0ab9$11177e390e333e27337721a1e8434796c23953cfdad01829f3aa0855130a44e5', 'Nam', 'default_avatar.png', 3, 0, NOW());

-- ========================================================
-- SEED DATA: Categories (2-tier Tree Structure)
-- ========================================================
-- Parent Categories (Chủ đề cấp 1)
INSERT INTO `categories` (`id`, `name`, `parent_id`, `description`, `created_at`) VALUES
(1, 'Luyện thi TOEIC', NULL, 'Các dạng bài thi chuẩn hóa TOEIC Reading & Listening', NOW()),
(2, 'Luyện thi TOEFL', NULL, 'Ngữ pháp học thuật và cấu trúc câu cho kỳ thi TOEFL iBT/ITP', NOW()),
(3, 'Tiếng Anh Chứng chỉ A, B, C', NULL, 'Chương trình chứng chỉ quốc gia A, B, C theo khung chuẩn', NOW()),
(4, 'Thì & Cấu trúc câu Tổng quát', NULL, 'Hệ thống 12 thì và quy tắc ngữ pháp căn bản đến nâng cao', NOW());

-- Sub-categories (Chủ đề con cấp 2)
INSERT INTO `categories` (`id`, `name`, `parent_id`, `description`, `created_at`) VALUES
(5, 'Part 5 - Hoàn thành câu (Incomplete Sentences)', 1, 'Kiểm tra từ vựng và ngữ pháp trọng tâm TOEIC Part 5', NOW()),
(6, 'Part 6 - Hoàn thành đoạn văn (Text Completion)', 1, 'Điền từ và ngữ pháp theo ngữ cảnh đoạn văn TOEIC', NOW()),
(7, 'Sentence Structure & Grammar', 2, 'Nhận diện cấu trúc mệnh đề chính, phụ và cụm từ TOEFL', NOW()),
(8, 'Written Expression & Error Identification', 2, 'Tìm lỗi sai ngữ pháp trong bài thi học thuật TOEFL', NOW()),
(9, 'Chứng chỉ A - Căn bản', 3, 'Ngữ pháp vỡ lòng và giao tiếp sơ cấp', NOW()),
(10, 'Chứng chỉ B - Trung cấp', 3, 'Ngữ pháp trung cấp và kỹ năng viết thư, đoạn văn', NOW()),
(11, 'Chứng chỉ C - Nâng cao', 3, 'Ngữ pháp phức tạp và thuật ngữ tiếng Anh chuyên ngành', NOW());

-- ========================================================
-- SEED DATA: 30 Rich-text Grammar Questions
-- ========================================================
INSERT INTO `questions` (`id`, `content`, `option_1`, `option_2`, `option_3`, `option_4`, `correct_option`, `explanation`, `level_id`, `category_id`, `created_at`) VALUES

-- --- BEGINNER (Rank 1) ---
(1, 
 '<p>My sister usually <strong>______</strong> up at 6:00 AM every weekday to prepare for work.</p>',
 'wake', 'wakes', 'waking', 'is waking', 2,
 '<p><strong>Giải thích:</strong> Trạng từ tần suất <em>usually</em> và cụm từ <em>every weekday</em> là dấu hiệu của <strong>Thì Hiện tại đơn</strong> diễn tả thói quen lặp đi lặp lại. Chủ ngữ <em>My sister</em> là ngôi thứ ba số ít nên động từ thêm <strong>-s</strong> (<em>wakes</em>).</p>',
 1, 4, NOW()),

(2, 
 '<p>Could you please pass me <strong>______</strong> apple on the fruit basket?</p>',
 'a', 'an', 'the', 'some', 2,
 '<p><strong>Giải thích:</strong> Danh từ <em>apple</em> bắt đầu bằng một nguyên âm (/ˈæp.əl/), vì vậy khi ở dạng số ít đếm được chưa xác định ta sử dụng mạo từ <strong>an</strong>.</p>',
 1, 9, NOW()),

(3, 
 '<p>The international seminar will officially start <strong>______</strong> 9:00 AM on Monday morning.</p>',
 'at', 'in', 'on', 'by', 1,
 '<p><strong>Giải thích:</strong> Quy tắc giới từ chỉ thời gian: dùng <strong>at</strong> trước mốc giờ cụ thể trong ngày (<em>at 9:00 AM</em>), dùng <em>on</em> trước thứ/ngày, và <em>in</em> trước tháng/năm/mùa.</p>',
 1, 5, NOW()),

(4, 
 '<p>This is my new laptop. Where did you put <strong>______</strong>?</p>',
 'your', 'yours', 'it', 'its', 3,
 '<p><strong>Giải thích:</strong> Đại từ tân ngữ <strong>it</strong> thay thế cho danh từ giống đực/cái chỉ đồ vật số ít đã được đề cập trước đó (<em>my new laptop</em>).</p>',
 1, NULL, NOW()),

(5, 
 '<p>Listen! The children <strong>______</strong> quietly in their bedroom upstairs.</p>',
 'sleep', 'are sleeping', 'slept', 'have slept', 2,
 '<p><strong>Giải thích:</strong> Câu bắt đầu bằng lời kêu gọi chú ý <em>Listen!</em> (dấu chấm than), báo hiệu một hành động đang trực tiếp xảy ra tại thời điểm nói -> dùng <strong>Thì Hiện tại tiếp diễn</strong>: <em>are sleeping</em>.</p>',
 1, 4, NOW()),

(6, 
 '<p>How <strong>______</strong> glasses of water do you drink on a daily basis?</p>',
 'much', 'many', 'long', 'often', 2,
 '<p><strong>Giải thích:</strong> <em>glasses of water</em> là cụm danh từ đếm được số nhiều. Để hỏi số lượng danh từ đếm được ta dùng <strong>How many</strong> (dùng <em>How much</em> cho danh từ không đếm được).</p>',
 1, 9, NOW()),

-- --- ELEMENTARY (Rank 2) ---
(7, 
 '<p>Last night, our family <strong>______</strong> an extraordinary movie at the cinema.</p>',
 'watch', 'watches', 'watched', 'watching', 3,
 '<p><strong>Giải thích:</strong> Dấu hiệu <em>Last night</em> (tối qua) chỉ thời điểm đã chấm dứt trong quá khứ -> Dùng <strong>Thì Quá khứ đơn</strong> (V2/V-ed): <em>watched</em>.</p>',
 2, 4, NOW()),

(8, 
 '<p>Mount Everest is significantly <strong>______</strong> than any other mountain on Earth.</p>',
 'high', 'higher', 'highest', 'more high', 2,
 '<p><strong>Giải thích:</strong> Cấu trúc <strong>so sánh hơn</strong> của tính từ ngắn (1 âm tiết): <em>adj-er + than</em>. Tính từ <em>high</em> trở thành <strong>higher</strong>.</p>',
 2, 7, NOW()),

(9, 
 '<p>You haven\'t completed the quarterly financial report yet, <strong>______</strong>?</p>',
 'haven\'t you', 'have you', 'do you', 'did you', 2,
 '<p><strong>Giải thích:</strong> Quy tắc <strong>Câu hỏi đuôi (Tag question)</strong>: Mệnh đề chính ở thể phủ định (<em>haven\'t completed</em>) thì phần câu hỏi đuôi phải ở thể khẳng định tương ứng (<strong>have you</strong>).</p>',
 2, 5, NOW()),

(10, 
 '<p>Due to the sudden rainstorm, we decided to stay <strong>______</strong> home.</p>',
 'in', 'on', 'at', 'with', 3,
 '<p><strong>Giải thích:</strong> Cụm cố định chỉ nơi chốn thông dụng: <strong>at home</strong> (ở nhà), tương tự như <em>at school, at work</em>.</p>',
 2, NULL, NOW()),

(11, 
 '<p>Passengers <strong>______</strong> fasten their seat belts securely during takeoff and landing.</p>',
 'must', 'can', 'may', 'might', 1,
 '<p><strong>Giải thích:</strong> Động từ khuyết thiếu <strong>must</strong> diễn tả quy định bắt buộc, mệnh lệnh pháp lý hoặc nguyên tắc an toàn nghiêm ngặt trên chuyến bay.</p>',
 2, 5, NOW()),

(12, 
 '<p>She bought a <strong>______</strong> car after receiving her year-end promotion.</p>',
 'new red Japanese', 'Japanese new red', 'red new Japanese', 'new Japanese red', 1,
 '<p><strong>Giải thích:</strong> Quy tắc trật tự tính từ <strong>OSASCOMP</strong>: Age (<em>new</em>) -> Color (<em>red</em>) -> Origin (<em>Japanese</em>). Do đó thứ tự chuẩn xác là <em>new red Japanese</em>.</p>',
 2, 10, NOW()),

-- --- PRE-INTERMEDIATE (Rank 3) ---
(13, 
 '<p>Mr. Jonathan has worked as a senior software consultant for this enterprise <strong>______</strong> 2018.</p>',
 'for', 'since', 'in', 'during', 2,
 '<p><strong>Giải thích:</strong> Trong <strong>Thì Hiện tại hoàn thành</strong>, dùng <strong>since</strong> trước một mốc thời gian cụ thể trong quá khứ (<em>since 2018</em>), dùng <em>for</em> trước một khoảng thời gian (ví dụ: <em>for 6 years</em>).</p>',
 3, 5, NOW()),

(14, 
 '<p>If it <strong>______</strong> sunny tomorrow afternoon, we will host an outdoor barbecue party.</p>',
 'is', 'will be', 'was', 'were', 1,
 '<p><strong>Giải thích:</strong> <strong>Câu điều kiện loại 1 (First Conditional)</strong> diễn tả sự việc có thật hoặc có thể xảy ra ở hiện tại/tương lai. Mệnh đề <em>If</em> chia ở Thì Hiện tại đơn (<em>is</em>), mệnh đề chính dùng <em>will + V-infinitive</em>.</p>',
 3, 4, NOW()),

(15, 
 '<p>The experienced engineer <strong>______</strong> repaired our main assembly line was praised by the director.</p>',
 'which', 'who', 'whom', 'whose', 2,
 '<p><strong>Giải thích:</strong> Đại từ quan hệ <strong>who</strong> dùng để thay thế cho danh từ chỉ người (<em>The experienced engineer</em>) và giữ chức năng làm chủ ngữ của mệnh đề quan hệ đứng sau.</p>',
 3, 7, NOW()),

(16, 
 '<p>The marketing manager strongly suggested <strong>______</strong> a consumer survey before launching the campaign.</p>',
 'conduct', 'to conduct', 'conducting', 'conducted', 3,
 '<p><strong>Giải thích:</strong> Cấu trúc động từ theo sau: động từ <em>suggest</em> khi không có tân ngữ trực tiếp đi kèm sẽ đi với <strong>V-ing (Danh động từ - Gerund)</strong>: <em>suggest doing something</em>.</p>',
 3, 5, NOW()),

(17, 
 '<p>The iconic Sydney Opera House <strong>______</strong> by Danish architect Jørn Utzon in the mid-20th century.</p>',
 'designed', 'was designed', 'is designed', 'has been designed', 2,
 '<p><strong>Giải thích:</strong> Câu bị động ở Thì Quá khứ đơn: <strong>S + was/were + V3/V-ed + (by O)</strong>. Vì chủ ngữ là công trình kiến trúc số ít và hành động diễn ra trong quá khứ nên dùng <em>was designed</em>.</p>',
 3, 10, NOW()),

(18, 
 '<p><strong>______</strong> the severe financial crisis, the innovative startup managed to turn a profit.</p>',
 'Although', 'Even though', 'Despite', 'Because', 3,
 '<p><strong>Giải thích:</strong> <em>the severe financial crisis</em> là một cụm danh từ (Noun Phrase). Để chỉ sự tương phản đi kèm cụm danh từ, ta dùng <strong>Despite</strong> hoặc <em>In spite of</em> (<em>Although/Even though</em> phải đi với một mệnh đề S+V).</p>',
 3, 6, NOW()),

-- --- INTERMEDIATE (Rank 4) ---
(19, 
 '<p>If I <strong>______</strong> enough capital right now, I would invest heavily in green renewable energy.</p>',
 'have', 'had', 'have had', 'would have', 2,
 '<p><strong>Giải thích:</strong> <strong>Câu điều kiện loại 2 (Second Conditional)</strong> giả định điều không có thật hoặc trái ngược với thực tế ở hiện tại. Cấu trúc mệnh đề If: <em>If + S + V2/V-ed</em> -> chọn <strong>had</strong> (mệnh đề chính: <em>would + V</em>).</p>',
 4, 4, NOW()),

(20, 
 '<p>The prominent pharmaceutical company, <strong>______</strong> headquarters is located in Basel, announced a medical breakthrough.</p>',
 'which', 'whose', 'where', 'that', 2,
 '<p><strong>Giải thích:</strong> <strong>whose</strong> là đại từ quan hệ chỉ quyền sở hữu, đứng giữa hai danh từ (<em>company</em> và <em>headquarters</em> - trụ sở của công ty đó).</p>',
 4, 8, NOW()),

(21, 
 '<p>By the time the rescue team arrived at the hazardous site, the trapped miners <strong>______</strong> for over ten hours.</p>',
 'waited', 'have waited', 'had been waiting', 'are waiting', 3,
 '<p><strong>Giải thích:</strong> Cấu trúc với <em>By the time + S + V-past</em>: hành động đợi đã diễn ra liên tục kéo dài trước thời điểm đội cứu hộ đến trong quá khứ -> Dùng <strong>Thì Quá khứ hoàn thành tiếp diễn (Past Perfect Continuous)</strong>: <em>had been waiting</em>.</p>',
 4, 7, NOW()),

(22, 
 '<p>He looked utterly exhausted after the exam. He <strong>______</strong> burning the midnight oil for weeks.</p>',
 'must have been', 'can\'t have been', 'should have been', 'needn\'t have been', 1,
 '<p><strong>Giải thích:</strong> Dùng <strong>must have + V3/V-ed</strong> để diễn đạt một suy đoán hợp lý và chắc chắn gần như 100% về một hành động đã xảy ra trong quá khứ dựa trên bằng chứng cụ thể (<em>looked utterly exhausted</em>).</p>',
 4, 11, NOW()),

(23, 
 '<p>Had the board members reviewed the contractual terms carefully, they <strong>______</strong> into such a dispute.</p>',
 'would not enter', 'would not have entered', 'will not enter', 'had not entered', 2,
 '<p><strong>Giải thích:</strong> Đây là dạng <strong>đảo ngữ của Câu điều kiện loại 3</strong>: <em>Had + S + V3/V-ed, S + would/could + have + V3/V-ed</em>. Diễn tả sự việc trái ngược với thực tế trong quá khứ.</p>',
 4, 5, NOW()),

(24, 
 '<p>We take immense pride in <strong>______</strong> our quarterly sales targets despite unfavorable market conditions.</p>',
 'achieve', 'achieved', 'having achieved', 'to achieve', 3,
 '<p><strong>Giải thích:</strong> Sau giới từ <em>in</em> cần một V-ing. Cụm phân từ hoàn thành <strong>having achieved</strong> được sử dụng để nhấn mạnh việc hoàn thành chỉ tiêu doanh số đã xảy ra trước thời điểm tự hào.</p>',
 4, NULL, NOW()),

-- --- ADVANCE (Rank 5) ---
(25, 
 '<p>Rarely <strong>______</strong> such breathtaking panoramic vistas during our mountaineering expedition.</p>',
 'we encountered', 'did we encounter', 'have we encounter', 'we did encounter', 2,
 '<p><strong>Giải thích:</strong> <strong>Đảo ngữ với trạng từ mang nghĩa phủ định/hiếm khi (Rarely, Seldom, Scarcely)</strong> đứng đầu câu: <em>Rarely + trợ động từ + S + V-nguyên mẫu</em>. Ở thì quá khứ đơn mượn trợ động từ <em>did</em> -> <strong>did we encounter</strong>.</p>',
 5, 7, NOW()),

(26, 
 '<p>The government inspection committee demanded that the hazardous chemical plant <strong>______</strong> operations immediately.</p>',
 'suspended', 'suspends', 'suspend', 'is suspending', 3,
 '<p><strong>Giải thích:</strong> <strong>Thể giả định (Subjunctive Mood)</strong> sau các động từ yêu cầu, đề nghị (<em>demand, insist, propose, recommend + that + S + (should) + V-bare infinitive</em>). Động từ <strong>suspend</strong> phải giữ nguyên thể không chia.</p>',
 5, 8, NOW()),

(27, 
 '<p><strong>______</strong> for the timely intervention of the paramedic, the patient might not have survived.</p>',
 'Were it not', 'Had it not been', 'If it was not', 'Should it not be', 2,
 '<p><strong>Giải thích:</strong> Cấu trúc đảo ngữ câu điều kiện loại 3 mang nghĩa "Nếu không nhờ có...": <strong>Had it not been for + Noun phrase</strong> (= <em>If it hadn\'t been for...</em>).</p>',
 5, 11, NOW()),

(28, 
 '<p><strong>______</strong> from the prestigious university with highest honors, Elena was immediately recruited by a Fortune 500 company.</p>',
 'Graduating', 'Having graduated', 'Graduated', 'To graduate', 2,
 '<p><strong>Giải thích:</strong> <strong>Rút gọn mệnh đề phân từ hoàn thành (Perfect Participle Clause)</strong>: dùng <em>Having + V3/V-ed</em> để nhấn mạnh hành động tốt nghiệp đã hoàn tất trọn vẹn trước khi hành động tuyển dụng diễn ra.</p>',
 5, 6, NOW()),

(29, 
 '<p>No sooner had the keynote speaker stepped onto the stage <strong>______</strong> the auditorium erupted in thunderous applause.</p>',
 'when', 'than', 'then', 'hardly', 2,
 '<p><strong>Giải thích:</strong> Cấu trúc đảo ngữ tương quan chỉ sự việc vừa mới xảy ra thì sự việc khác ập đến: <strong>No sooner had + S + V3/V-ed THAN + S + V2/V-ed</strong> (ngay khi... thì...). Cần phân biệt với <em>Hardly/Scarcely... WHEN</em>.</p>',
 5, 8, NOW()),

(30, 
 '<p>It was not until midnight <strong>______</strong> the weary travelers finally arrived at their remote destination.</p>',
 'when', 'that', 'which', 'than', 2,
 '<p><strong>Giải thích:</strong> <strong>Cấu trúc câu chẻ (Cleft sentence)</strong> nhấn mạnh thời gian: <strong>It is/was not until + mốc thời gian + THAT + S + V</strong> (Mãi cho đến khi... thì...). Chú ý bắt buộc dùng liên từ <em>that</em>.</p>',
 5, 11, NOW());

-- ========================================================
-- SEED DATA: Sample Exam Attempts for Leaderboard Demo
-- ========================================================
-- Attempt 1 by mai_anh (Score 100)
INSERT INTO `exam_attempts` (`id`, `user_id`, `category_id`, `attempt_number`, `total_questions`, `correct_count`, `wrong_count`, `score`, `duration_seconds`, `started_at`, `completed_at`) VALUES
(1, 3, 1, 1, 10, 10, 0, 100.00, 245, DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)),
(2, 3, 5, 2, 10, 9, 1, 90.00, 310, DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)),
(3, 2, 4, 1, 10, 8, 2, 80.00, 420, DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)),
(4, 4, 3, 1, 10, 7, 3, 70.00, 510, DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY));

-- Details for Attempt 1
INSERT INTO `exam_attempt_details` (`attempt_id`, `question_id`, `selected_option`, `is_correct`, `question_order`) VALUES
(1, 19, 2, 1, 1), (1, 20, 2, 1, 2), (1, 21, 3, 1, 3), (1, 22, 1, 1, 4), (1, 23, 2, 1, 5),
(1, 24, 3, 1, 6), (1, 13, 2, 1, 7), (1, 14, 1, 1, 8), (1, 15, 2, 1, 9), (1, 16, 3, 1, 10);
