from datetime import datetime, timedelta, timezone
import os
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from backend.app.database import users_collection as mongo_users_collection

users_collection = mongo_users_collection

# ============================================================
# JWT CONFIGURATION
# ============================================================

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    raise RuntimeError("Set JWT_SECRET_KEY to a random secret of at least 32 characters in .env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# ============================================================
# PASSWORD HASHING
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ============================================================
# OAUTH2
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token"
)


# ============================================================
# PYDANTIC MODELS
# ============================================================

class Token(BaseModel):
    access_token: str
    token_type: str
    role: Optional[str] = None


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = "patient"
    disabled: Optional[bool] = None
    doctor_id: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None
    hospital: Optional[str] = None


class UserInDB(User):
    hashed_password: str


# ============================================================
# LEGACY PATIENT DEMO ACCOUNT
# ============================================================

# Compatibility for older callers; all accounts must exist in MongoDB.
fake_users_db = {}


# ============================================================
# MONGODB USER
# ============================================================

def get_mongo_user(username: str) -> Optional[dict]:

    normalized = (username or "").strip().lower()
    if not normalized:
        return None

    user_dict = users_collection.find_one({
        "$or": [
            {"username": normalized},
            {"email": normalized},
        ]
    })

    if not user_dict:
        return None

    # Remove MongoDB ObjectId because it is not needed
    user_dict.pop("_id", None)

    return user_dict


# ============================================================
# PASSWORD FUNCTIONS
# ============================================================

def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def get_password_hash(password: str) -> str:

    return pwd_context.hash(password)


# ============================================================
# GET USER FROM LEGACY DEMO DATA
# ============================================================

def get_user(
    db: dict,
    username: str
) -> Optional[UserInDB]:

    username = username.strip().lower()

    if username in db:

        user_dict = db[username]

        return UserInDB(
            **user_dict
        )

    return None


# ============================================================
# AUTHENTICATE USER
# ============================================================

def authenticate_user(
    db: dict,
    username: str,
    password: str
) -> Optional[UserInDB]:

    username = username.strip().lower()

    # --------------------------------------------------------
    # FIRST: CHECK MONGODB
    # --------------------------------------------------------

    mongo_user = get_mongo_user(username)

    if mongo_user:

        if not mongo_user.get("hashed_password"):
            return False

        user = UserInDB(
            **mongo_user
        )

        if not verify_password(
            password,
            user.hashed_password
        ):
            return False

        return user

    # --------------------------------------------------------
    # SECOND: CHECK THE LEGACY PATIENT DEMO ACCOUNT.
    # Doctor accounts are stored exclusively in MongoDB.
    # --------------------------------------------------------

    user = get_user(
        db,
        username
    )

    if not user:
        return False

    if not verify_password(
        password,
        user.hashed_password
    ):
        return False

    return user


# ============================================================
# CREATE ACCESS TOKEN
# ============================================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:

    to_encode = data.copy()

    if expires_delta:

        expire = (
            datetime.now(timezone.utc)
            + expires_delta
        )

    else:

        expire = (
            datetime.now(timezone.utc)
            + timedelta(minutes=15)
        )

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


# ============================================================
# GET CURRENT USER
# ============================================================

def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username)

    except JWTError:
        raise credentials_exception

    # First check MongoDB
    mongo_user = get_mongo_user(token_data.username)

    if mongo_user:
        try:
            return User(
                username=mongo_user["username"],
                email=mongo_user.get("email"),
                full_name=mongo_user.get("full_name"),
                role=mongo_user.get("role", "patient"),
                disabled=mongo_user.get("disabled"),
                doctor_id=mongo_user.get("doctor_id"),
                specialization=mongo_user.get("specialization"),
                license_number=mongo_user.get("license_number"),
                phone=mongo_user.get("phone"),
                hospital=mongo_user.get("hospital"),
            )
        except Exception:
            raise credentials_exception

    raise credentials_exception

# ============================================================
# ACTIVE USER
# ============================================================

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:

    if current_user.disabled:
        raise HTTPException(
            status_code=400,
            detail="Inactive user"
        )

    return current_user


def get_current_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform this action.",
        )
    return current_user
