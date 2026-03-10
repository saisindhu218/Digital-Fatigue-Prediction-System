import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta
import secrets
from config import settings

class QRService:
    @staticmethod
    def generate_qr_token(user_id: str, device_type: str) -> dict:
        """Generate QR token for device pairing"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.QR_CODE_EXPIRY_MINUTES
        )
        
        # Create QR code
        qr_data = f"fatigue-app:{token}:{user_id}:{device_type}"
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