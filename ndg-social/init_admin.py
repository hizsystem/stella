"""
첫 배포 시 관리자 계정 자동 생성.
이미 계정이 있으면 아무것도 하지 않음.
"""
import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_EMAIL = os.getenv("INIT_ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.getenv("INIT_ADMIN_PASSWORD", "")
ADMIN_NAME = os.getenv("INIT_ADMIN_NAME", "관리자")

if not ADMIN_EMAIL or not ADMIN_PASSWORD:
    print("[init_admin] INIT_ADMIN_EMAIL / INIT_ADMIN_PASSWORD 미설정 → 건너뜀")
else:
    from backend.database import create_tables, SessionLocal, User
    import bcrypt as _bcrypt

    create_tables()
    db = SessionLocal()
    try:
        if db.query(User).first():
            print("[init_admin] 기존 사용자 존재 → 건너뜀")
        else:
            hashed = _bcrypt.hashpw(
                ADMIN_PASSWORD.encode("utf-8")[:72], _bcrypt.gensalt()
            ).decode("utf-8")
            admin = User(
                email=ADMIN_EMAIL,
                name=ADMIN_NAME,
                hashed_password=hashed,
                role="admin",
            )
            db.add(admin)
            db.commit()
            print(f"[init_admin] 관리자 계정 생성 완료: {ADMIN_EMAIL}")
    finally:
        db.close()
