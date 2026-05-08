import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.settings import settings


async def send_password_reset_email(to_email: str, reset_token: str) -> None:
    reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"

    message = MIMEMultipart("alternative")
    message["Subject"] = "Восстановление пароля"
    message["From"] = settings.smtp_from_email
    message["To"] = to_email

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
      <h2 style="color: #1d4ed8;">Восстановление пароля</h2>
      <p>Вы получили это письмо, потому что запросили сброс пароля для вашей учётной записи.</p>
      <p style="margin: 24px 0;">
        <a href="{reset_url}"
           style="background:#1d4ed8;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;">
          Сбросить пароль
        </a>
      </p>
      <p style="color:#6b7280;font-size:14px;">Ссылка действительна в течение 1 часа.</p>
      <p style="color:#6b7280;font-size:14px;">Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>
    </body>
    </html>
    """

    message.attach(MIMEText(html_body, "html"))

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_password,
        use_tls=settings.smtp_use_tls,
    )
