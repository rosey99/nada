from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

import logging

from nada.deps import SessionDep
from nada.models import TokenData, User, UserInDB
from nada.settings import settings


logger = logging.getLogger(__name__)

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


async def get_user(db: SessionDep, username: str):
    #h_password = await db.hget(name=f"nada:users:{username}", key="hashed_password")
    h_password, is_active, user_id = await db.hmget(name=f"nada:users:{username}", keys=["hashed_password", "is_active", "id"])
    if h_password:
        user_dict = {"hashed_password": h_password, "is_active": is_active, "id": user_id}
        return UserInDB(**user_dict)


async def authenticate_user(db: SessionDep, username: str, password: str):
    user = await get_user(db=db, username=username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None):
    to_encode = {"sub": subject}
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user_from_cookie(db: SessionDep, request: Request) -> User:
    """
    Get the current user from the cookies in a request.

    Use this function from inside other routes to get the current user. Good
    for views that should work for both logged in, and not logged in users.
    """
    token = request.cookies.get(settings.COOKIE_NAME, None)
    logger.debug(f'Got a cookie token: {token}')
    user = None
    token_user = None
    if token:
        token = token.split(" ")[1]
        token_user = get_current_user(db=db, token=token)
    if token_user:
        user = token_user
    logger.debug(f'Got a cookie user: {token_user}')
    return user


async def get_current_user(db: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def create_user(db: SessionDep, user_data: User, password: str):
    # credentials_exception = HTTPException(
    #     status_code=status.HTTP_401_UNAUTHORIZED,
    #     detail="Could not validate credentials",
    #     headers={"WWW-Authenticate": "Bearer"},
    # )
    logger.info(f'creating User: {user_data["username"]}')
    try:
        user = User(**user_data)

        existing_user = await get_user(db, username=user.username)
        if existing_user is None:
            # TODO serialization in redis client is not working/built-in
            #  for bool and uuid types
            data = user.model_dump(serialize_as_any=True)
            data['hashed_password'] = get_password_hash(password)
            data['id'] = data['id'].hex
            await db.hset(f"nada:users:{user.username}", mapping=data)
            logger.info(f"Successfully created user: {user.username}")
            #raise credentials_exception
        else:
            logger.info(f"User with username: {user.username} already exists")
    finally:
        pass
    return user

# Depends
CurrentCookieUser = Annotated[User, Depends(get_current_user_from_cookie)]
