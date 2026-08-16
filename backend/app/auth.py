from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from backend.app.database import users_collection


# ============================================================
# JWT CONFIGURATION
# ============================================================

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
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


class UserInDB(User):
    hashed_password: str


# ============================================================
# EXISTING USERS
# ============================================================

fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "role": "doctor",
        "hashed_password": "$2b$12$zA6ilqwM1GzNkijm9iVnVeklyeG9sp1EGuuoSwhlMcN9jxJujKhOu",
    },

    "doctor": {
        "username": "doctor",
        "full_name": "Doctor User",
        "email": "doctor@gmail.com",
        "role": "doctor",
        "hashed_password": "$2b$12$TdGJQoxKf1wBsv.Ksm2Nneqn0z5TUNQPMl4j2/nJ.yGhOhn8P36le",
    },

    "patient": {
        "username": "patient",
        "full_name": "Patient User",
        "email": "patient@example.com",
        "role": "patient",
        "hashed_password": "$2b$12$Fw7DAAMZ3.GJExtd/yw6CehbXW/K1Yc04ZYCTEPBcNVgB0SL/yqMy",
    }
}


# ============================================================
# MONGODB USER
# ============================================================

def get_mongo_user(username: str) -> Optional[dict]:

    username = username.strip().lower()

    user_dict = users_collection.find_one({
        "username": username
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
# GET USER FROM FAKE DATABASE
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
    # SECOND: CHECK EXISTING FAKE USERS
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

async def get_current_user(
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
            )
        except Exception:
            raise credentials_exception

    # Fallback to fake users
    fake_user = get_user(
        fake_users_db,
        token_data.username
    )

    if fake_user is None:
        raise credentials_exception

    return User(
        username=fake_user.username,
        email=fake_user.email,
        full_name=fake_user.full_name,
        role=fake_user.role,
        disabled=fake_user.disabled,
    )

# ============================================================
# ACTIVE USER
# ============================================================

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:

    if current_user.disabled:
        raise HTTPException(
            status_code=400,
            detail="Inactive user"
        )

    return current_user