from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

import logging

from nada.deps import SessionDep
from nada.models import TokenData, User, UserInDB
from nada.settings import settings


logger = logging.getLogger(__name__)

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

CredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


async def get_user(db: SessionDep, username: str):
    #h_password = await db.hget(name=f"nada:users:{username}", key="hashed_password")
    h_password, is_active, user_id = await db.hmget(name=f"nada:users:{username}", keys=["hashed_password", "is_active", "id"])
    if h_password:
        user_dict = {"hashed_password": h_password.decode(), "is_active": is_active, "id": user_id, "username": username}
        return UserInDB(**user_dict)


async def authenticate_user(db: SessionDep, username: str, password: str):
    user = await get_user(db=db, username=username)
    if not user:
        logger.info(f"User does not exist: {username}")
        return False
    logger.info(f"stored password: {user.hashed_password} -> hashed: {get_password_hash(password)}")
    if not verify_password(password, user.hashed_password):
        logger.info(f"Password verification failed for {username}")
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


async def get_current_user_from_cookie(db: SessionDep, request: Request) -> User:
    """
    Get the current user from the cookies in a request.

    Use this function from inside other routes to get the current user. Good
    for views that should work for both logged in, and not logged in users.
    """
    token = request.cookies.get(settings.COOKIE_NAME, None)
    logger.info(f'Got a cookie token: {token}')
    user = None
    token_user = None
    if token:
        token = token.split(" ")[1]
        token_user = await get_current_user(db=db, token=token, raise_on_fail=False)
    if token_user is not CredentialsException:
        user = token_user
    else:
        #raise credentials_exception
        logger.info("Redirecting to login")
        return RedirectResponse(url='/agent/v1/login', status_code=303)
    logger.info(f'Got a cookie user: {token_user}')
    return user


async def get_current_user(db: SessionDep, token: Annotated[str, Depends(oauth2_scheme)], raise_on_fail: bool = True):
    result = None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            result = CredentialsException
    except InvalidTokenError:
        result = CredentialsException
    if not result:
        token_data = TokenData(username=username)
        user = await get_user(db, username=token_data.username)
        result = user if user is not None else CredentialsException
    if raise_on_fail and result is CredentialsException:
        raise result
    return result


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def create_user(db: SessionDep, user_data: User, password: str):
    logger.info(f'creating User: {user_data["username"]}')
    try:
        user = User(**user_data)

        existing_user = await get_user(db, username=user.username)
        if existing_user is not None:
            logger.warning(f"User with username: {user.username} already exists, overwriting")

        # TODO serialization in redis client is not working/built-in
        #  for bool and uuid types
        data = user.model_dump(serialize_as_any=True)
        hash = get_password_hash(password)
        data['hashed_password'] = hash
        data['id'] = data['id'].hex
        await db.hset(f"{settings.DEFAULT_TENANT}:users:{user.username}", mapping=data)
        logger.info(f"Successfully created user: {user.username}")

    finally:
        # TODO for later, pref hooks might go here
        pass
    return user

# Depends
CurrentCookieUser = Annotated[User, Depends(get_current_user_from_cookie)]
