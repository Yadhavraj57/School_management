from typing import List
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import auth, crud, models, schemas
from app.database import get_db

app = FastAPI(title="School Management API")


# ==========================================
# Auth Endpoints
# ==========================================

@app.post(
    "/auth/signup",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(user_data: schemas.UserSignup, db: Session = Depends(get_db)):
    return crud.register_user(db, user_data)


@app.post("/auth/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    access_token = auth.create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


# ==========================================
# Student Endpoints (Full CRUD)
# ==========================================

@app.post(
    "/students/",
    response_model=schemas.StudentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth.require_roles("admin", "principal"))],
)
def create_student(
    student_data: schemas.StudentAdminCreate,
    db: Session = Depends(get_db),
):
    return crud.create_student_with_account(db, student_data)


@app.get(
    "/students/",
    response_model=List[schemas.StudentResponse],
    dependencies=[Depends(auth.require_roles("admin", "principal", "teacher"))],
)
def read_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_students(db, skip=skip, limit=limit)


@app.get(
    "/students/{student_id}",
    response_model=schemas.StudentResponse,
    dependencies=[Depends(auth.get_current_user)],
)
def read_student(student_id: int, db: Session = Depends(get_db)):
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


@app.put(
    "/students/{student_id}",
    response_model=schemas.StudentResponse,
    dependencies=[Depends(auth.require_roles("admin", "principal"))],
)
def update_student(
    student_id: int,
    student_data: schemas.StudentUpdate,
    db: Session = Depends(get_db),
):
    return crud.update_student(db, student_id, student_data)


@app.delete(
    "/students/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth.require_roles("admin", "principal"))],
)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    crud.delete_student(db, student_id)
    return None


# ==========================================
# Teacher Endpoints (Full CRUD)
# ==========================================

@app.post(
    "/teachers/",
    response_model=schemas.TeacherResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth.require_roles("admin", "principal"))],
)
def create_teacher(
    teacher_data: schemas.TeacherAdminCreate,
    db: Session = Depends(get_db),
):
    return crud.create_teacher_with_account(db, teacher_data)


@app.get(
    "/teachers/",
    response_model=List[schemas.TeacherResponse],
    dependencies=[Depends(auth.require_roles("admin", "principal"))],
)
def read_teachers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_teachers(db, skip=skip, limit=limit)


@app.get(
    "/teachers/{teacher_id}",
    response_model=schemas.TeacherResponse,
    dependencies=[Depends(auth.get_current_user)],
)
def read_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = crud.get_teacher(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return teacher


@app.put(
    "/teachers/{teacher_id}",
    response_model=schemas.TeacherResponse,
    dependencies=[Depends(auth.require_roles("admin", "principal"))],
)
def update_teacher(
    teacher_id: int,
    teacher_data: schemas.TeacherUpdate,
    db: Session = Depends(get_db),
):
    return crud.update_teacher(db, teacher_id, teacher_data)


@app.delete(
    "/teachers/{teacher_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth.require_roles("admin", "principal"))],
)
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    crud.delete_teacher(db, teacher_id)
    return None


# ==========================================
# Subject Enrollment Endpoints
# ==========================================

@app.post("/students/{student_id}/subjects/{subject_id}/enroll")
def enroll_student(
    student_id: int,
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles("admin", "principal", "teacher")),
):
    crud.enroll_student_in_subject(db, student_id, subject_id, current_user)
    return {"detail": "Student successfully enrolled in subject"}


@app.post("/students/{student_id}/subjects/{subject_id}/unenroll")
def unenroll_student(
    student_id: int,
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles("admin", "principal", "teacher")),
):
    crud.unenroll_student_from_subject(db, student_id, subject_id, current_user)
    return {"detail": "Student successfully unenrolled from subject"}