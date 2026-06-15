"""Autenticación del dashboard: login con JWT y dependencia de usuario actual."""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse, UsuarioOut
from app.utils.responses import api_error

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


# ------------------------------------------------------------- utilidades hash
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(plano: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plano, hashed)
    except Exception:
        return False


def crear_token(sub: str) -> str:
    expira = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {"sub": sub, "exp": expira}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decodificar_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# --------------------------------------------------------------- dependencias
def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> Usuario:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise api_error("NO_AUTORIZADO", "Token no proporcionado", 401)
    token = authorization.split(" ", 1)[1]
    email = decodificar_token(token)
    if not email:
        raise api_error("TOKEN_INVALIDO", "Token inválido o expirado", 401)
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        raise api_error("USUARIO_NO_ENCONTRADO", "Usuario no existe", 401)
    return usuario


# -------------------------------------------------------------------- rutas
@router.post("/login", response_model=TokenResponse)
def login(datos: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if not usuario or not verificar_password(datos.password, usuario.password_hash):
        raise api_error("CREDENCIALES_INVALIDAS", "Email o contraseña incorrectos", 401)
    token = crear_token(usuario.email)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UsuarioOut)
def me(usuario: Usuario = Depends(get_current_user)):
    return UsuarioOut(id=str(usuario.id), email=usuario.email)
