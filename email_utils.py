
import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    MAIL_USERNAME: EmailStr | str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", os.getenv("MAIL_USERNAME", ""))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_TLS: bool = os.getenv("MAIL_TLS", "True").lower() == "true"
    MAIL_SSL: bool = os.getenv("MAIL_SSL", "False").lower() == "true"

settings = Settings()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_STARTTLS=settings.MAIL_TLS,
    MAIL_SSL_TLS=settings.MAIL_SSL,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fm = FastMail(conf)

async def send_email(subject: str, recipients: list[str], body_html: str, attachments: list[tuple[str, bytes, str]] | None = None):
    try:
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=body_html,
            subtype=MessageType.html
        )
        if attachments:
            # Each attachment: (filename, content_bytes, mime_type)
            message.attachments = []
            for filename, content, mime in attachments:
                message.attachments.append({
                    "file": content,
                    "headers": {"Content-Disposition": f'attachment; filename="{filename}"'},
                    "mime_type": mime
                })
        await fm.send_message(message)
        return True
    except Exception as e:
        print("Email send failed:", e)
        return False
