import io
from typing import List, Tuple, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from models import db, Question, Level, Category

HEADER_COLUMNS = [
    "Cau_hoi",
    "Lua_chon_1",
    "Lua_chon_2",
    "Lua_chon_3",
    "Lua_chon_4",
    "Dap_an_dung (1-4)",
    "Giai_thich",
    "Level",
    "Chu_de_id (tùy chọn)"
]

def generate_excel_template() -> io.BytesIO:
    """
    Generates a professionally formatted Excel (.xlsx) template
    containing predefined headers and 2 sample grammar questions.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Question Template"

    # Styling definitions
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    sample_font = Font(name="Arial", size=10)
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9")
    )

    # 1. Write Header Row
    for col_idx, col_name in enumerate(HEADER_COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
    ws.row_dimensions[1].height = 28

    # 2. Write 2 Sample Rows
    samples = [
        [
            "She ______ to school by bus every morning.",
            "go",
            "goes",
            "going",
            "went",
            2,
            "Chủ ngữ ngôi thứ ba số ít 'She' ở thì Hiện tại đơn (every morning) nên động từ 'go' thêm 'es' thành 'goes'.",
            "Beginner",
            ""  # Để trống = dùng chung
        ],
        [
            "If I ______ you, I would take that opportunity immediately.",
            "was",
            "were",
            "am",
            "have been",
            2,
            "Câu điều kiện loại 2 (giả định trái ngược với hiện tại). Với mệnh đề If, động từ to be dùng 'were' cho tất cả các ngôi trong ngữ pháp chuẩn.",
            "Intermediate",
            1  # Gán cho chủ đề có ID = 1
        ]
    ]

    for row_idx, sample_data in enumerate(samples, start=2):
        ws.row_dimensions[row_idx].height = 24
        for col_idx, val in enumerate(sample_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = sample_font
            cell.border = thin_border
            if col_idx == 6:  # Dap an dung
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx in (8, 9):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # 3. Auto-adjust column widths
    column_widths = {
        1: 45,  # Cau hoi
        2: 18,  # Lua chon 1
        3: 18,  # Lua chon 2
        4: 18,  # Lua chon 3
        5: 18,  # Lua chon 4
        6: 18,  # Dap an dung
        7: 45,  # Giai thich
        8: 18,  # Level
        9: 22   # Chu de id
    }
    for col_idx, width in column_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # Save to memory buffer
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def import_questions_from_excel(file_stream) -> Tuple[int, List[str]]:
    """
    Parses and validates questions from an uploaded .xlsx file.
    Validates every row strictly. If errors exist, no questions are inserted and errors are returned.
    
    Returns:
        (imported_count, list_of_error_messages)
    """
    errors: List[str] = []
    questions_to_create: List[Question] = []

    try:
        wb = openpyxl.load_workbook(file_stream, data_only=True)
    except Exception as e:
        return 0, [f"Không thể đọc file Excel. Định dạng không hợp lệ hoặc file bị hỏng: {str(e)}"]

    ws = wb.active
    if not ws:
        return 0, ["File Excel không có sheet nào để xử lý."]

    # Pre-cache levels for fast lookup (case-insensitive name & rank_order & id)
    levels = Level.query.all()
    level_lookup = {}
    for lvl in levels:
        level_lookup[str(lvl.id)] = lvl
        level_lookup[lvl.name.strip().lower()] = lvl
        level_lookup[str(lvl.rank_order)] = lvl

    # Pre-cache categories for fast lookup
    categories = Category.query.all()
    category_ids = {cat.id for cat in categories}

    total_rows = ws.max_row
    if total_rows < 2:
        return 0, ["File Excel không có dữ liệu để import (chỉ có dòng tiêu đề hoặc rỗng)."]

    for row_idx in range(2, total_rows + 1):
        # Read columns 1 to 9
        row_vals = [ws.cell(row=row_idx, column=c).value for c in range(1, 10)]

        # Check if entire row is empty
        if all(v is None or str(v).strip() == "" for v in row_vals):
            continue

        cau_hoi = str(row_vals[0]).strip() if row_vals[0] is not None else ""
        opt_1 = str(row_vals[1]).strip() if row_vals[1] is not None else ""
        opt_2 = str(row_vals[2]).strip() if row_vals[2] is not None else ""
        opt_3 = str(row_vals[3]).strip() if row_vals[3] is not None else ""
        opt_4 = str(row_vals[4]).strip() if row_vals[4] is not None else ""
        dap_an_val = row_vals[5]
        giai_thich = str(row_vals[6]).strip() if row_vals[6] is not None else ""
        level_val = str(row_vals[7]).strip() if row_vals[7] is not None else ""
        chu_de_val = row_vals[8]

        row_errors = []

        # Validate Question text
        if not cau_hoi:
            row_errors.append("Nội dung câu hỏi không được để trống")

        # Validate Options
        if not opt_1 or not opt_2 or not opt_3 or not opt_4:
            row_errors.append("Phải nhập đầy đủ cả 4 lựa chọn (Lựa chọn 1, 2, 3, 4)")

        # Validate Correct Option (1-4)
        correct_opt = None
        try:
            if dap_an_val is None or str(dap_an_val).strip() == "":
                row_errors.append("Đáp án đúng không được để trống")
            else:
                correct_opt = int(float(str(dap_an_val).strip()))
                if correct_opt not in (1, 2, 3, 4):
                    row_errors.append(f"Đáp án đúng phải là số nguyên từ 1 đến 4 (giá trị hiện tại: '{dap_an_val}')")
        except (ValueError, TypeError):
            row_errors.append(f"Đáp án đúng không hợp lệ: '{dap_an_val}' (phải là số 1, 2, 3 hoặc 4)")

        # Validate Level
        matched_level = None
        if not level_val:
            row_errors.append("Cột Level không được để trống")
        else:
            matched_level = level_lookup.get(level_val.lower())
            if not matched_level:
                valid_level_names = ", ".join([lvl.name for lvl in levels])
                row_errors.append(f"Level '{level_val}' không tồn tại. Danh sách level hợp lệ: {valid_level_names}")

        # Validate Category (optional)
        matched_cat_id = None
        if chu_de_val is not None and str(chu_de_val).strip() != "":
            try:
                parsed_cat_id = int(float(str(chu_de_val).strip()))
                if parsed_cat_id not in category_ids:
                    row_errors.append(f"Chủ đề ID '{parsed_cat_id}' không tồn tại trong hệ thống")
                else:
                    matched_cat_id = parsed_cat_id
            except (ValueError, TypeError):
                row_errors.append(f"Chủ đề ID không hợp lệ: '{chu_de_val}' (phải là số nguyên hoặc để trống)")

        if row_errors:
            errors.append(f"Dòng {row_idx}: " + "; ".join(row_errors))
        else:
            question = Question(
                content=cau_hoi,
                option_1=opt_1,
                option_2=opt_2,
                option_3=opt_3,
                option_4=opt_4,
                correct_option=correct_opt,
                explanation=giai_thich,
                level_id=matched_level.id,
                category_id=matched_cat_id
            )
            questions_to_create.append(question)

    if errors:
        return 0, errors

    if not questions_to_create:
        return 0, ["Không tìm thấy dữ liệu hợp lệ nào để import."]

    try:
        db.session.add_all(questions_to_create)
        db.session.commit()
        return len(questions_to_create), []
    except Exception as e:
        db.session.rollback()
        return 0, [f"Lỗi cơ sở dữ liệu khi lưu dữ liệu: {str(e)}"]
