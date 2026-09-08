from datetime import date
from typing import List, Optional
from pydantic import BaseModel, EmailStr


# ==========================================
# User & Auth Schemas
# ==========================================

class UserBase(BaseModel):
    email: EmailStr


class UserSignup(UserBase):
    name: str
    password: str
    role: str = "student"
    class_id: Optional[int] = None
    dob: Optional[date] = None
    phone_number: Optional[str] = None


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# ==========================================
# Student Schemas
# ==========================================

class StudentBase(BaseModel):
    name: str
    email: EmailStr
    class_id: Optional[int] = None
    dob: Optional[date] = None
    phone_number: Optional[str] = None


class StudentAdminCreate(StudentBase):
    password: str


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    class_id: Optional[int] = None
    dob: Optional[date] = None
    phone_number: Optional[str] = None


class StudentResponse(StudentBase):
    id: int
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


# ==========================================
# Teacher Schemas
# ==========================================

class TeacherBase(BaseModel):
    name: str
    email: EmailStr


class TeacherAdminCreate(TeacherBase):
    password: str


class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class TeacherResponse(TeacherBase):
    id: int
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


# ==========================================
# Subject Schemas
# ==========================================

class SubjectBase(BaseModel):
    name: str
    teacher_id: Optional[int] = None


class SubjectResponse(SubjectBase):
    id: int

    class Config:
        from_attributes = True