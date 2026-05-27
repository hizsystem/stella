import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt as _bcrypt
from sqlalchemy.orm import Session

from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.database import User, get_db
from backend.schemas import UserCreate, UserOut, Token, LoginRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(pw: str) -> str:
    return _bcrypt.hashpw(pw.encode("utf-8")[:72], _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))


def create_access_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({**data, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    # 토큰 없으면 기본 사용자(id=1)로 자동 인증
    if not token:
        user = db.query(User).first()
        if user:
            return user
        raise HTTPException(status_code=401, detail="인증 실패")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        logger.info(f"[AUTH] sub={user_id!r} type={type(user_id).__name__}")
        if user_id is None:
            logger.warning("[AUTH] sub is None → fallback to default user")
            user = db.query(User).first()
            if user:
                return user
            raise HTTPException(status_code=401, detail="인증 실패")
        user_id = int(user_id)
    except JWTError as e:
        logger.warning(f"[AUTH] JWTError: {e} → fallback to default user")
        user = db.query(User).first()
        if user:
            return user
        raise HTTPException(status_code=401, detail="토큰이 유효하지 않습니다")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"[AUTH] user id={user_id} not found → fallback to default user")
        user = db.query(User).first()
        if user:
            return user
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")
    return user


def require_role(roles: list[str]):
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="권한이 없습니다")
        return current_user
    return checker


@router.post("/register", response_model=UserOut)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
    user = User(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
