"""
Minimal Authentication module for the LangGraph Sales/Inventory System.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr


# Configuration
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

# Data storage (in-memory for simplicity)
users_db = {}
user_id_counter = 1


# Models
class User(BaseModel):
    id: int
    email: EmailStr
    username: str
    full_name: str
    is_active: bool = True
    created_at: datetime
    role: str = "user"


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: User


class UserInDB(User):
    hashed_password: str


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user(username: str) -> Optional[UserInDB]:
    """Get user by username."""
    return users_db.get(username)


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(user_data: UserCreate) -> UserInDB:
    """Create a new user."""
    global user_id_counter

    # Check if user already exists
    if user_data.username in users_db:
        raise ValueError("Username already registered")

    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = UserInDB(
        id=user_id_counter,
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        created_at=datetime.utcnow(),
        is_active=True,
        role="user",
    )

    users_db[user_data.username] = user
    user_id_counter += 1

    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserInDB:
    """Get current user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Initialize with a default user
def init_default_user():
    """Initialize with a default user."""
    if not users_db:
        default_user = UserCreate(
            email="admin@example.com",
            username="admin",
            password="admin123",
            full_name="Administrator",
        )
        create_user(default_user)


# Initialize
init_default_user()
