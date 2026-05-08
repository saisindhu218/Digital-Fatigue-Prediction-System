import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta
import secrets
import socket
from src.config import settings


def get_local_ip():
    """Get current machine IP dynamically (works for any WiFi/hotspot)"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # external DNS (no actual connection needed)
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class QRService:
    @staticmethod
    def generate_qr_token(user_id: str, device_type: str) -> dict:
        """Generate QR token for device pairing"""

        token = secrets.token_urlsafe(32)

        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.QR_CODE_EXPIRY_MINUTES
        )

        # 🔥 Dynamic IP (no manual change needed)
        local_ip = get_local_ip()

        qr_data = f"http://{local_ip}:8000/api/v1/pairing/scan?token={token}"

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffered = BytesIO()
        img.save(buffered, format="PNG")

        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()

        qr_code_url = f"data:image/png;base64,{qr_code_base64}"

        return {
            "token": token,
            "qr_code_url": qr_code_url,
            "expires_at": expires_at,
            "user_id": user_id,
            "device_type": device_type
        }

    @staticmethod
    def verify_qr_token(token: str, stored_token: str, expires_at: datetime) -> bool:
        """Verify if QR token is valid"""

        if datetime.utcnow() > expires_at:
            return False

        return secrets.compare_digest(token, stored_token)