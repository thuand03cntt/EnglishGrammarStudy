import logging
from flask import current_app, render_template_string
from flask_mail import Mail, Message

mail = Mail()
logger = logging.getLogger("EnglishPractice.MailService")

RESET_EMAIL_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f8fafc; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .header { text-align: center; border-bottom: 2px solid #3b82f6; padding-bottom: 20px; margin-bottom: 20px; }
        .header h2 { color: #1e3a8a; margin: 0; }
        .btn { display: inline-block; padding: 12px 24px; background-color: #2563eb; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 20px; }
        .footer { margin-top: 30px; font-size: 12px; color: #64748b; text-align: center; }
        .token-box { background: #f1f5f9; padding: 12px; border-radius: 4px; font-family: monospace; word-break: break-all; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Luyện Thi Ngữ Pháp Tiếng Anh</h2>
        </div>
        <p>Xin chào <strong>{{ username }}</strong>,</p>
        <p>Hệ thống nhận được yêu cầu đặt lại mật khẩu cho tài khoản liên kết với địa chỉ email <strong>{{ email }}</strong>.</p>
        <p>Vui lòng bấm vào nút bên dưới để tạo mật khẩu mới (liên kết có hiệu lực trong 30 phút):</p>
        <div style="text-align: center;">
            <a href="{{ reset_url }}" class="btn" target="_blank">Đặt Lại Mật Khẩu</a>
        </div>
        <p style="margin-top: 25px;">Hoặc bạn có thể sao chép liên kết này vào trình duyệt:</p>
        <div class="token-box">{{ reset_url }}</div>
        <p style="margin-top: 20px; color: #dc2626; font-size: 13px;">* Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này. Tài khoản của bạn vẫn an toàn.</p>
        <div class="footer">
            <p>&copy; 2026 Hệ thống Luyện thi Ngữ pháp Tiếng Anh. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

def send_reset_password_email(user, reset_url: str) -> bool:
    """
    Sends a password reset link to user email via Flask-Mail SMTP.
    Falls back gracefully to console logging if SMTP is not configured or fails.
    """
    suppress_send = current_app.config.get("MAIL_SUPPRESS_SEND", False)
    mail_username = current_app.config.get("MAIL_USERNAME", "")

    # Dev/Test fallback logger
    console_notice = (
        f"\n{'='*75}\n"
        f" [PASSWORD RESET EMAIL - CONSOLE LOG & TEST MODE]\n"
        f" To: {user.email} (Username: {user.username})\n"
        f" Reset URL: {reset_url}\n"
        f" Note: Link valid for 30 minutes.\n"
        f"{'='*75}\n"
    )

    if suppress_send or not mail_username:
        print(console_notice)
        logger.info(console_notice)
        return True

    try:
        msg = Message(
            subject="[English Practice] Yêu cầu đặt lại mật khẩu",
            recipients=[user.email],
            sender=current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@englishpractice.local")
        )
        msg.html = render_template_string(
            RESET_EMAIL_HTML_TEMPLATE,
            username=user.username,
            email=user.email,
            reset_url=reset_url
        )
        msg.body = (
            f"Xin chào {user.username},\n\n"
            f"Vui lòng truy cập đường dẫn sau để đặt lại mật khẩu của bạn:\n"
            f"{reset_url}\n\n"
            f"Liên kết có hiệu lực trong vòng 30 phút."
        )
        mail.send(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send email via SMTP: {str(e)}")
        # Print fallback so developers / reviewers can still complete testing
        print(console_notice)
        print(f"[SMTP Warning] Could not send via server: {e}. Outputting reset link to console above.")
        return True
