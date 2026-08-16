import jwt
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import Device, User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="No autenticado")
    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario inválido o desactivado")
    return user


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Sin permisos para esta operación")
        return user

    return dependency


def get_device_by_key(
    x_device_key: str | None = Header(default=None, alias="X-Device-Key"),
    db: Session = Depends(get_db),
) -> Device:
    """Autenticación del sensor por device key (pública, sin JWT)."""
    if not x_device_key:
        raise HTTPException(status_code=401, detail="Falta header X-Device-Key")
    device = db.query(Device).filter(Device.api_key == x_device_key).first()
    if device is None:
        raise HTTPException(status_code=401, detail="Device key inválida")
    return device
