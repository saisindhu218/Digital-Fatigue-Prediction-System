# Make routes a proper package
from .auth import router as auth_router
from .pairing import router as pairing_router
from .usage import router as usage_router
# Only import prediction if you want to use it
from .prediction import router as prediction_router

__all__ = ["auth_router", "pairing_router", "usage_router", "prediction_router"]