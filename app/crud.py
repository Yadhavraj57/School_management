from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_password_hash


# ==========================================
# Auth & User Operations
# ==========================================

def register_user(db: Session, user_data: schemas.UserSignup) -> models.User:
    if user_data.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public signup is only available for students. Teachers and staff must be created by administrators.",
        )

    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    if user_data.class_id:
        class_obj = db.query(models.Class).filter(models.Class.id == user_data.class_id).first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned class does not exist.",
            )

    try:
        new_user = models.User(
            username=user_data.email,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            role="student",
            is_active=True,
        )
        db.add(new_user)
        db.flush()

        new_student = models.Student(
            user_id=new_user.id,
            name=user_data.name,
            email=user_data.email,
            class_id=user_data.class_id,
            dob=user_data.dob,
            phone_number=user_data.phone_number,
        )
        db.add(new_student)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity violation: {str(exc.orig)}",
        )
    except Exception:
        db.rollback()
        raise


def update_user_role(db: Session, user_id: int, new_role: str):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Changing user roles is not allowed to preserve profile consistency.",
    )


# ==========================================
# Student CRUD Operations
# ==========================================

def create_student_with_account(db: Session, student_data: schemas.StudentAdminCreate) -> models.Student:
    if db.query(models.User).filter(models.User.email == student_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    if student_data.class_id:
        class_obj = db.query(models.Class).filter(models.Class.id == student_data.class_id).first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target class does not exist.",
            )

    try:
        user = models.User(
            username=student_data.email,
            email=student_data.email,
            hashed_password=get_password_hash(student_data.password),
            role="student",
            is_active=True,
        )
        db.add(user)
        db.flush()

        student = models.Student(
            user_id=user.id,
            name=student_data.name,
            email=student_data.email,
            class_id=student_data.class_id,
            dob=student_data.dob,
            phone_number=student_data.phone_number,
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        return student
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(exc.orig)}",
        )
    except Exception:
        db.rollback()
        raise


def get_students(db: Session, skip: int = 0, limit: int = 100) -> List[models.Student]:
    return db.query(models.Student).offset(skip).limit(limit).all()


def get_student(db: Session, student_id: int) -> Optional[models.Student]:
    return db.query(models.Student).filter(models.Student.id == student_id).first()


def update_student(
    db: Session,
    student_id: int,
    student_update: schemas.StudentUpdate,
) -> models.Student:
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found.",
        )

    update_data = student_update.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != student.email:
        existing = db.query(models.User).filter(models.User.email == update_data["email"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use.",
            )
        if student.user:
            student.user.email = update_data["email"]

    if "class_id" in update_data and update_data["class_id"] is not None:
        class_obj = db.query(models.Class).filter(models.Class.id == update_data["class_id"]).first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target class does not exist.",
            )

    try:
        for key, value in update_data.items():
            setattr(student, key, value)
        db.commit()
        db.refresh(student)
        return student
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc.orig),
        )
    except Exception:
        db.rollback()
        raise


def delete_student(db: Session, student_id: int) -> None:
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found.",
        )

    try:
        if student.user:
            db.delete(student.user)
        db.delete(student)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc.orig),
        )
    except Exception:
        db.rollback()
        raise


# ==========================================
# Teacher CRUD Operations
# ==========================================

def create_teacher_with_account(db: Session, teacher_data: schemas.TeacherAdminCreate) -> models.Teacher:
    if db.query(models.User).filter(models.User.email == teacher_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    try:
        user = models.User(
            username=teacher_data.email,
            email=teacher_data.email,
            hashed_password=get_password_hash(teacher_data.password),
            role="teacher",
            is_active=True,
        )
        db.add(user)
        db.flush()

        teacher = models.Teacher(
            user_id=user.id,
            name=teacher_data.name,
            email=teacher_data.email,
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        return teacher
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(exc.orig)}",
        )
    except Exception:
        db.rollback()
        raise


def get_teachers(db: Session, skip: int = 0, limit: int = 100) -> List[models.Teacher]:
    return db.query(models.Teacher).offset(skip).limit(limit).all()


def get_teacher(db: Session, teacher_id: int) -> Optional[models.Teacher]:
    return db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()


def update_teacher(
    db: Session,
    teacher_id: int,
    teacher_update: schemas.TeacherUpdate,
) -> models.Teacher:
    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found.",
        )

    update_data = teacher_update.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != teacher.email:
        existing = db.query(models.User).filter(models.User.email == update_data["email"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use.",
            )
        if teacher.user:
            teacher.user.email = update_data["email"]

    try:
        for key, value in update_data.items():
            setattr(teacher, key, value)
        db.commit()
        db.refresh(teacher)
        return teacher
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc.orig),
        )
    except Exception:
        db.rollback()
        raise


def delete_teacher(db: Session, teacher_id: int) -> None:
    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found.",
        )

    try:
        if teacher.user:
            db.delete(teacher.user)
        db.delete(teacher)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc.orig),
        )
    except Exception:
        db.rollback()
        raise


# ==========================================
# Subject Enrollment Operations
# ==========================================

def enroll_student_in_subject(
    db: Session,
    student_id: int,
    subject_id: int,
    current_user: models.User,
) -> models.Student:
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")

    if current_user.role == "teacher":
        teacher = db.query(models.Teacher).filter(models.Teacher.user_id == current_user.id).first()
        if not teacher or subject.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers can only enroll students in subjects they teach.",
            )

    if subject in student.subjects:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is already enrolled in this subject.",
        )

    try:
        student.subjects.append(subject)
        db.commit()
        db.refresh(student)
        return student
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc.orig))
    except Exception:
        db.rollback()
        raise


def unenroll_student_from_subject(
    db: Session,
    student_id: int,
    subject_id: int,
    current_user: models.User,
) -> models.Student:
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")

    if current_user.role == "teacher":
        teacher = db.query(models.Teacher).filter(models.Teacher.user_id == current_user.id).first()
        if not teacher or subject.teacher_id != teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers can only unenroll students from subjects they teach.",
            )

    if subject not in student.subjects:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is not enrolled in this subject.",
        )

    try:
        student.subjects.remove(subject)
        db.commit()
        db.refresh(student)
        return student
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc.orig))
    except Exception:
        db.rollback()
        raise