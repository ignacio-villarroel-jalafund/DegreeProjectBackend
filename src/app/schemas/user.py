from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserUpdateDetails(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UserUpdate(BaseModel):
    is_active: Optional[bool] = None

class UserInDBBase(UserBase):
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserUpdatePassword(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str
