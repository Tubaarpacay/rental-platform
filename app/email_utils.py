# -------------------------------------------------
# E-posta Gönderme İşlemleri (Resend)
# -------------------------------------------------

import os
import resend

from dotenv import load_dotenv

# -------------------------------------------------
# .env dosyasını yükle
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# Resend API Key
# -------------------------------------------------
resend.api_key = os.getenv("RESEND_API_KEY")


# -------------------------------------------------
# Şifre Sıfırlama Maili Gönder
# -------------------------------------------------
def send_password_reset_email(
    receiver_email: str,
    reset_link: str
):
    """
    Kullanıcıya şifre sıfırlama bağlantısı içeren
    e-postayı Resend servisi üzerinden gönderir.
    """

    params = {
        "from": "Eşya Kiralama <onboarding@resend.dev>",
        "to": [receiver_email],
        "subject": "Şifre Sıfırlama",
        "html": f"""
        <h2>Şifre Sıfırlama</h2>

        <p>
            Şifrenizi sıfırlamak için aşağıdaki butona tıklayın.
        </p>

        <p>
            <a href="{reset_link}">
                Şifremi Sıfırla
            </a>
        </p>

        <p>
            Eğer bu isteği siz yapmadıysanız bu e-postayı dikkate almayabilirsiniz.
        </p>
        """
    }

    return resend.Emails.send(params)