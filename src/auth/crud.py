from fastapi import Depends, FastAPI, Header, HTTPException

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import schemas
from src.auth.models import AuthUser, UserSettings
from src.auth.schemas import UserCreateInput
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_token_header(token: str = Header(...)):
    if token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="Invalid token provided")
    return token

async def add_user(user: UserCreateInput, session: AsyncSession):
    stmt = (
        insert(AuthUser)
        .values(
            {
                AuthUser.email: user.email,
                AuthUser.hashed_password: user.password,
            },
        )
        .returning(AuthUser)
    )

    user = (await session.execute(stmt)).scalar_one_or_none()
    await session.commit()
    return user


async def get_user_profile(
    user: AuthUser,
    session: AsyncSession,) -> schemas.UserProfile:
    """Get user profile."""
    print(AuthUser.email)
    stmt = select(UserSettings).filter_by(user_id=user.id)
    profile = await session.execute(stmt)
    return schemas.UserProfile.validate(profile.scalars().first())


async def update_user_profile(
    data: schemas.UserProfileUpdate,
    user: AuthUser,
    session: AsyncSession,
) -> schemas.UserProfile:
    """Update user profile."""
    stmt = (
        update(UserSettings)
        .filter_by(user_id=user.id)
        .values(data.dict())
        .returning(UserSettings)
    )
    profile = await session.execute(stmt)
    await session.commit()
    return schemas.UserProfile.validate(profile.scalars().first())


async def create_user_profile(user: AuthUser, session: AsyncSession):
    """Create user profile."""
    stmt = insert(UserSettings).values(
        {
            UserSettings.user_id: user.id,
        },
    )
    await session.execute(stmt)
    await session.commit()
