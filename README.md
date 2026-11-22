# EnglishPractice - Hệ Thống Luyện Thi Ngữ Pháp Tiếng Anh Thông Minh

Ứng dụng web Monolithic luyện thi ngữ pháp tiếng Anh (quy mô ~100 người dùng đồng thời/tổng thể), tối ưu tốc độ phát triển, thuật toán chọn câu hỏi thông minh và dễ dàng triển khai chỉ bằng Docker.

---

## 🚀 Công Nghệ Sử Dụng
- **Backend:** Python 3.11+, Flask 3.x, Flask-SQLAlchemy, Flask-Login, Flask-Mail, Werkzeug.
- **Frontend:** HTML5, Bootstrap 5.3, Bootstrap Icons, Vanilla JS, Rich Text Editor (**Quill.js** qua CDN).
- **Cơ sở dữ liệu:** **MariaDB 10.11+** (driver `PyMySQL`), hỗ trợ fallback SQLite để chạy thử nghiệm nhanh.
- **Xử lý Excel:** `openpyxl` (tạo file mẫu `.xlsx` chuẩn và import dữ liệu hàng loạt có validation nghiêm ngặt).
- **Gửi Email:** `Flask-Mail` (SMTP) hỗ trợ Quên mật khẩu kèm chế độ fallback log ra terminal console.
- **Triển khai:** Docker, `docker-compose.yml`, Gunicorn WSGI.

---

## 🌟 Tính Năng Nổi Bật

### I. Phân hệ Thí sinh (Candidate)
1. **Đăng ký & Hồ sơ:**
   - Đăng ký nhanh: `username` (duy nhất), `email` (duy nhất), `password` (hash bảo mật), `gender` (Nam/Nữ/Khác), `avatar` (upload ảnh đại diện lưu tại `static/uploads/avatars/`, có avatar mặc định), `level_id` (chọn từ 5 Level: *Beginner*, *Elementary*, *Pre-intermediate*, *Intermediate*, *Advance*).
   - Trang hồ sơ cá nhân: cập nhật ảnh đại diện, trình độ, đổi mật khẩu và xem thống kê tổng câu đúng, số lượt thi.
2. **Đăng nhập & Quên mật khẩu:**
   - Đăng nhập linh hoạt bằng `username` hoặc `email`.
   - Quên mật khẩu: tạo token đặt lại mật khẩu gửi qua email; tự động in đường link reset ra console terminal ở chế độ dev/test để thử nghiệm ngay lập tức.
3. **Thiết lập & Làm bài thi:**
   - Chọn **Chủ đề luyện tập cấp 1** (*Luyện thi TOEIC, Thi TOEFL, Tiếng Anh Bằng A, B, C, Thì & Cấu trúc tổng quát...*).
   - Chọn **Chủ đề con cấp 2** (tự động tải động theo danh mục cha, ví dụ: *TOEIC -> Part 5, Part 6...*).
   - Chọn **Số lượng câu hỏi**: `10`, `20`, `50`, `100` câu.
   - **Giao diện làm bài thi chuyên nghiệp:**
     - Đồng hồ đếm thời gian thực tế (tính bằng giây).
     - **Phân trang 10 câu / trang** bằng JavaScript, giữ nguyên trạng thái câu trả lời đã chọn qua lại giữa các trang và tự động sao lưu vào `localStorage` chống mất bài khi lỡ F5.
     - Thanh điều hướng **Question Palette** bên phải: bấm nhảy nhanh đến câu hỏi bất kỳ, câu đã chọn đáp án tự động chuyển sang màu xanh.
     - Mỗi câu hỏi gồm nội dung Rich Text HTML và 4 lựa chọn Radio (chỉ chọn 1).
4. **Nộp bài, Chấm điểm & Xem lại:**
   - Chấm điểm chuẩn thang **100**: `score = round((correct_count / total_questions) * 100, 2)`.
   - Hiển thị rõ ràng: Điểm số, Tổng số câu đúng, **Tổng số câu sai (bôi đỏ đậm)**, thời gian làm bài.
   - Hiển thị **phần giải thích lý thuyết chi tiết** (dịch nghĩa, cấu trúc ngữ pháp) cho từng câu.
   - **Lịch sử làm bài:** Lưu trữ toàn bộ các lượt thi; cho phép xem lại chi tiết từng đề đã thi với highlight xanh (đáp án đúng) / đỏ (đáp án sai của thí sinh).
5. **Bảng xếp hạng (Trang chủ):**
   - Xếp hạng Top 10 thí sinh xuất sắc nhất dựa trên **tổng số câu trả lời đúng cộng dồn qua tất cả các lượt thi** (Avatar, Username, Level, Số lượt thi, Tổng số câu đúng).

### II. Phân hệ Quản trị (Admin)
1. **Tài khoản Admin duy nhất:**
   - Toàn hệ thống có duy nhất 1 tài khoản quản trị (`username: admin`), mật khẩu mặc định là `123456a@`.
   - Trang Đổi mật khẩu Admin an toàn. Nghiêm cấm tạo thêm tài khoản admin từ giao diện ngoài.
2. **Quản lý Level:** CRUD cấu hình 5 Level từ Rank 1 đến Rank 5.
3. **Quản lý Chủ đề 2 cấp:** Cấu hình cây chủ đề 2 cấp (`parent_id = NULL` là chủ đề cấp 1; `parent_id != NULL` là chủ đề con cấp 2).
4. **Soạn thảo Câu hỏi (Rich Text):**
   - Form soạn thảo tích hợp **Quill.js Rich Text Editor** cho Nội dung câu hỏi và Phần giải thích chi tiết.
   - 4 ô lựa chọn trả lời và radio chọn đáp án đúng (1, 2, 3, 4).
   - Chọn Level độ khó và gán Chủ đề (hỗ trợ quy tắc: nếu không chọn chủ đề (`category_id IS NULL`), câu hỏi sẽ được dùng chung cho tất cả các chủ đề).
5. **Import Excel & Tải Template:**
   - Nút **Tải Template Excel** (`.xlsx`) chuẩn màu sắc, viền và 2 dòng dữ liệu mẫu chuẩn chỉ.
   - Upload file `.xlsx`, tự động validate từng dòng (báo lỗi cụ thể dòng nào nếu sai sót) và import hàng loạt vào MariaDB.

---

## 🧠 Thuật Toán Chọn Câu Hỏi Thông Minh

Khi thí sinh bắt đầu bài thi với tham số `(user_id, selected_category_id, question_count)`:
1. **Lọc theo chủ đề:**
   - Lấy câu hỏi thuộc `selected_category_id` (nếu chọn chủ đề cấp 1 có con, lấy cả câu hỏi của cha và các con) **CỘNG VỚI** các câu hỏi dùng chung (`category_id IS NULL`).
2. **Lọc theo Level phù hợp với trình độ thí sinh (`user_level_rank`):**
   - Ưu tiên câu hỏi có `question_level_rank <= user_level_rank`.
   - Nếu kho câu hỏi chưa đủ, cho phép nới lỏng tối đa `user_level_rank + 1`. Tuyệt đối **không** đưa câu hỏi `Intermediate` (rank 4) hoặc `Advance` (rank 5) cho thí sinh `Beginner` (rank 1).
3. **Phân nhóm ưu tiên chống trùng lặp & ôn tập câu sai:**
   - Phân tích lịch sử làm bài của thí sinh thành 3 nhóm:
     - **Nhóm 1 (Ưu tiên cao nhất):** Câu hỏi thí sinh **đã từng làm SAI** ở lần gần nhất + các câu hỏi **CHƯA TỪNG THI** bao giờ.
     - **Nhóm 2 (Ưu tiên trung bình):** Các câu hỏi đã từng làm đúng nhưng ở các lần thi cũ nhất trước đó.
     - **Nhóm 3 (Ưu tiên thấp nhất):** Các câu hỏi vừa mới làm đúng gần đây (trong 3 lần thi gần nhất).
   - Trộn ngẫu nhiên (`random.shuffle`) trong từng nhóm trước khi cắt lấy đúng `question_count` câu hỏi, sau đó shuffle lại toàn bộ đề thi để tạo cảm giác tự nhiên nhất.

---

## 📁 Cấu Trúc Thư Mục Dự Án

```
EnglishPractice/
├── app.py                      # Flask Application factory, CLI, Error handlers
├── config.py                   # Cấu hình môi trường (MariaDB, SQLite, Upload, Mail)
├── models.py                   # SQLAlchemy Models (User, Level, Category, Question, Attempts)
├── services/
│   ├── exam_generator.py       # Thuật toán chọn câu hỏi thông minh 3 nhóm ưu tiên
│   ├── excel_service.py        # Tạo template Excel và import hàng loạt với validate
│   └── mail_service.py         # Flask-Mail SMTP và fallback console logger
├── routes/
│   ├── auth.py                 # Đăng ký, Đăng nhập, Đổi avatar, Quên MK, Profile
│   ├── exam.py                 # Thiết lập đề, Làm bài, Nộp bài, Kết quả, Lịch sử, Bảng xếp hạng
│   └── admin.py                # Admin Dashboard, CRUD Level, Category, Question, Excel
├── database/
│   └── init_dump.sql           # MariaDB dump: DDL bảng, Admin mặc định, 5 Levels, 30 câu hỏi mẫu
├── templates/
│   ├── base.html               # Layout chuẩn Bootstrap 5, Navbar, Flash, Footer
│   ├── home/                   # Trang chủ & Bảng xếp hạng Top thí sinh
│   ├── auth/                   # Login, Register, Forgot/Reset Password, Profile
│   ├── exam/                   # Setup, Take (Timer + 10 câu/trang), Result, History, Review
│   └── admin/                  # Base admin, Dashboard, Levels, Categories, Questions, Excel
├── static/
│   ├── css/custom.css          # Styling giao diện hiện đại, responsive
│   ├── js/exam.js              # Timer thực tế, phân trang 10 câu, Palette, lưu state
│   ├── js/main.js              # Dropdown chủ đề động, preview avatar, alert
│   ├── img/default_avatar.png  # Avatar mặc định
│   └── uploads/avatars/        # Thư mục lưu avatar người dùng tải lên
├── Dockerfile                  # Đóng gói Python 3.11 Monolithic với Gunicorn
├── docker-compose.yml          # Dịch vụ web + MariaDB 10.11 tự động nạp init_dump.sql
├── .env.example                # File mẫu biến môi trường
├── .env                        # File biến môi trường đang dùng
├── requirements.txt            # Danh sách thư viện Python
└── README.md                   # Hướng dẫn chi tiết
```

---

## 🐳 Hướng Dẫn Triển Khai Bằng Docker (Khuyến nghị)

Chỉ cần cài đặt [Docker Desktop](https://www.docker.com/) trên máy và chạy:

### 1. Khởi chạy hệ thống
Mở terminal tại thư mục gốc dự án và chạy:
```bash
docker compose up -d --build
```

Container MariaDB 10.11 sẽ tự động chạy file `database/init_dump.sql` ngay lần đầu khởi tạo để nạp đầy đủ cấu trúc bảng, tài khoản admin, danh mục level, chủ đề 2 cấp và 30 câu hỏi ngữ pháp mẫu.

### 2. Truy cập ứng dụng
- **Trang chủ & Làm bài thi:** [http://localhost:5000](http://localhost:5000)
- **Tài khoản Quản trị viên (Admin):**
  - Tên đăng nhập: `admin`
  - Mật khẩu: `123456a@`
  - Trang đăng nhập: [http://localhost:5000/auth/login](http://localhost:5000/auth/login)
  - Trang quản trị: [http://localhost:5000/admin](http://localhost:5000/admin)

### 3. Dừng hệ thống
```bash
docker compose down
```
*(Nếu muốn xóa sạch dữ liệu volume DB để chạy lại từ đầu: `docker compose down -v`)*

---

## 💻 Hướng Dẫn Chạy Trực Tiếp Bằng Python Local

Nếu bạn muốn chạy trực tiếp không qua Docker:

### 1. Tạo môi trường ảo và cài đặt thư viện
```bash
# Tạo môi trường ảo Python 3.11+
python -m venv venv

# Kích hoạt môi trường ảo:
# Trên Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Trên Linux/macOS:
source venv/bin/activate

# Cài đặt các thư viện cần thiết:
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường `.env`
Sao chép từ `.env.example`:
```bash
cp .env.example .env
```
Mở file `.env` và điều chỉnh thông số kết nối:
- **Nếu dùng MariaDB / MySQL đã cài trên máy:**
  ```env
  DB_HOST=localhost
  DB_PORT=3306
  DB_USER=root
  DB_PASSWORD=your_password
  DB_NAME=english_practice_db
  USE_SQLITE=false
  ```
  *(Bạn có thể import file `database/init_dump.sql` vào MariaDB bằng lệnh: `mysql -u root -p english_practice_db < database/init_dump.sql`)*

- **Nếu muốn test nhanh KHÔNG CẦN cài MariaDB:**
  Đặt biến sau trong `.env`:
  ```env
  USE_SQLITE=true
  ```
  Ứng dụng sẽ tự động dùng SQLite (`database/english_practice.db`) và tự động khởi tạo admin mặc định cùng các level khi chạy!

### 3. Khởi tạo dữ liệu và chạy ứng dụng
```bash
# Khởi tạo bảng và tài khoản admin mặc định:
flask init-db

# Chạy ứng dụng web:
python app.py
```
Truy cập trình duyệt tại: **`http://localhost:5000`**

---

## 🧪 Kịch Bản Kiểm Thử Nhanh (Testing Checklist)

1. **Trang chủ:** Truy cập `http://localhost:5000`, quan sát Bảng xếp hạng Top thí sinh (dữ liệu mẫu từ `init_dump.sql` đã có sẵn các lượt thi demo).
2. **Đăng ký thí sinh:** Bấm "Đăng ký", điền form, tải ảnh đại diện và chọn Level (ví dụ: *Beginner*). Đăng ký xong hệ thống tự động đăng nhập.
3. **Luyện thi:** Bấm "Luyện thi", chọn chủ đề *Luyện thi TOEIC* -> *Part 5*, chọn 10 câu hỏi, bấm "Bắt đầu làm bài".
4. **Giao diện thi:** Kiểm tra đồng hồ đếm giây hoạt động, chuyển trang 1-10 bằng nút phân trang hoặc Question Palette, chọn đáp án và thấy nút palette đổi màu xanh.
5. **Nộp bài & Chấm điểm:** Bấm "Nộp bài", xác nhận trong modal. Xem điểm số, số câu đúng, **số câu sai bôi đỏ**, và đọc giải thích lý thuyết chi tiết của từng câu.
6. **Lịch sử thi:** Vào menu tài khoản -> "Lịch sử làm bài", bấm "Xem chi tiết" để xem lại bài thi vừa nộp.
7. **Đăng nhập Quản trị viên:** Đăng xuất tài khoản thí sinh, đăng nhập bằng `admin` / `123456a@`.
8. **Kiểm tra chức năng Admin:**
   - Vào "Danh mục Level": xem và chỉnh sửa 5 level.
   - Vào "Chủ đề luyện tập (2 cấp)": xem cây chủ đề TOEIC, TOEFL...
   - Vào "Ngân hàng Câu hỏi": lọc câu hỏi theo level/chủ đề, tìm kiếm từ khóa.
   - Bấm "Soạn câu hỏi mới": thử nghiệm trình soạn thảo **Quill.js Rich Text**, in đậm, màu sắc, tạo câu hỏi mới.
   - Vào "Import Excel": bấm "Tải File Template Mẫu (.xlsx)" để nhận file Excel mẫu chuẩn 9 cột, thử upload file và xem hệ thống validate.
   - Vào "Đổi mật khẩu Admin": đổi mật khẩu an toàn.
9. **Kiểm tra Quên mật khẩu:** Đăng xuất, bấm "Quên mật khẩu", nhập email đã đăng ký. Mở terminal đang chạy app/docker logs để xem liên kết reset password được in trực tiếp ra console.
