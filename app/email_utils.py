# -------------------------------------------------
# E-posta Gönderme İşlemleri (Gmail SMTP + fastapi-mail)
# -------------------------------------------------

import os
import logging

from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

# -------------------------------------------------
# .env dosyasını yükle
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# Log ayarı
# -------------------------------------------------
logger = logging.getLogger(__name__)


# -------------------------------------------------
# Mail bağlantı ayarları
# -------------------------------------------------
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS") == "True",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS") == "True",
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False
)


# -------------------------------------------------
# Şifre Sıfırlama Maili Gönder
# -------------------------------------------------
async def send_password_reset_email(
    receiver_email: str,
    reset_link: str
):
    """
    Kullanıcıya şifre sıfırlama bağlantısı içeren
    e-postayı Gmail SMTP üzerinden gönderir.
    """

    html_content = f"""
    <h2>Şifre Sıfırlama</h2>

    <p>Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın.</p>

    <p>
        <a href="{reset_link}">
            Şifremi Sıfırla
        </a>
    </p>

    <p>Bu isteği siz yapmadıysanız bu e-postayı dikkate almayabilirsiniz.</p>
    """

    message = MessageSchema(
        subject="Şifre Sıfırlama",
        recipients=[receiver_email],
        body=html_content,
        subtype="html"
    )

    try:
        fm = FastMail(conf)
        await fm.send_message(message)

    except Exception as error:
        logger.error(
            f"Şifre sıfırlama e-postası gönderilemedi: {error}"
        )


# -------------------------------------------------
# Hesap Doğrulama Maili Gönder
# -------------------------------------------------
async def send_verification_email(
    receiver_email: str,
    verification_link: str
):
    """
    Kullanıcıya hesap doğrulama bağlantısı içeren
    e-postayı Gmail SMTP üzerinden gönderir.
    """

    html_content = f"""
    <h2>Hesap Doğrulama</h2>

    <p>Hesabınızı doğrulamak için aşağıdaki bağlantıya tıklayın.</p>

    <p>
        <a href="{verification_link}">
            Hesabımı Doğrula
        </a>
    </p>

    <p>Bu hesabı siz oluşturmadıysanız bu e-postayı dikkate almayabilirsiniz.</p>
    """

    message = MessageSchema(
        subject="Hesabınızı Doğrulayın",
        recipients=[receiver_email],
        body=html_content,
        subtype="html"
    )

    try:
        fm = FastMail(conf)
        await fm.send_message(message)

    except Exception as error:
        logger.error(
            f"Hesap doğrulama e-postası gönderilemedi: {error}"
        )