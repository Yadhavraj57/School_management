# Student & School Management API: Comprehensive Developer Reference & Architecture Guide

This document provides an exhaustive, authoritative technical guide to the **Student & School Management API**.

It details the system architecture, explains every single application module in depth based on the current codebase, documents data models, schemas, authentication and Role-Based Access Control (RBAC), API endpoints, transaction flows, and database migrations with Alembic.

---

## 1. Project Architecture Overview

The application is built using a modern, asynchronous-capable Python backend stack designed for high performance, type safety, security, and clean separation of concerns:

* **API Framework**: [FastAPI](https://fastapi.tiangolo.com/) for high-performance REST endpoints with automatic OpenAPI interactive documentation (`/docs` and `/redoc`).
* **Authentication & Cryptography**: Direct [Bcrypt](https://pypi.org/project/bcrypt/) integration with explicit 72-byte truncation protection, and [python-jose](https://pypi.org/project/python-jose/) implementing JSON Web Tokens (JWT) through OAuth2 Password Bearer flow.
* **Role-Based Access Control (RBAC)**: A layered security model with 4 distinct roles (`admin`, `principal`, `teacher`, `student`) strictly enforced at the route dependency layer.
* **ORM (Object Relational Mapper)**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) managing relational mappings, connection pooling, and SQL compilation.
* **Data Validation & Serialization**: [Pydantic v2](https://docs.pydantic.dev/) for strict type validation, request parsing, and response serialization (`from_attributes = True`).
* **Database Migrations**: [Alembic](https://alembic.sqlalchemy.org/) maintaining linear, version-controlled PostgreSQL schema revisions.
* **Database & Driver**: [PostgreSQL](https://www.postgresql.org/) accessed via the [psycopg2-binary](https://pypi.org/project/psycopg2-binary/) adapter.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Application Layer                       │
│  ┌────────────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │   /auth (Signup/Login) │  │ /students CRUD │  │  /teachers CRUD  │  │
│  └────────────────────────┘  └────────────────┘  └──────────────────┘  │
│          │                           │                     │           │
│          ▼                           ▼                     ▼           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │     Security & RBAC Layer (OAuth2 Bearer JWT + require_roles)    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          CRUD & Business Logic                         │
│  ┌────────────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │ Account/Profile Sync   │  │ Student Ops    │  │ Enrollment Ops   │  │
│  └────────────────────────┘  └────────────────┘  └──────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    SQLAlchemy 2.0 ORM & Data Models                    │
│   User (1:1) ──> Student (M:1) ──> Class                             │
│   User (1:1) ──> Teacher (1:1) ──> Class (Class Teacher)               │
│   Teacher (1:M) ──> Subject (M:N) <── Student                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     PostgreSQL Relational Database                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory & File Structure

```text
Student_CRUD_Application/
│
├── app/
│   ├── __init__.py           # Package initializer
│   ├── database.py           # PostgreSQL Engine, SessionLocal, Base, and get_db dependency
│   ├── models.py             # SQLAlchemy ORM models (User, Student, Class, Teacher, Subject, student_subject)
│   ├── schemas.py            # Pydantic request/response schemas for Auth, Student, Teacher, Subject
│   ├── auth.py               # Bcrypt hashing, JWT token creation, get_current_user, and require_roles
│   ├── crud.py               # Business logic, DB operations, atomic user-profile creation, enrollments
│   ├── main.py               # FastAPI application setup, routes, status codes, and endpoint RBAC guards
│   └── seed_roles.py         # Database seeder for default Admin, Principal, and Teacher accounts
│
├── alembic/
│   ├── versions/             # Linear schema migration scripts
│   │   ├── 8944d7db6b33_create_students_table.py
│   │   ├── 232068afd9e1_add_dob_and_phone_number_to_students.py
│   │   ├── c1881ecb9503_create_classes_teachers_subjects_and_.py
│   │   ├── 21d66fd12994_add_class_teacher_to_class.py
│   │   └── a22fb04d03dd_add_users_table.py
│   ├── env.py                # Alembic runtime configuration & model metadata binder
│   └── script.py.mako        # Migration template
│
├── alembic.ini               # Alembic database connection & logging configuration
├── requirements.txt          # Python project dependencies
├── .env                      # Environment configuration (DATABASE_URL, SECRET_KEY, etc.)
├── .env.example              # Example environment configuration template
├── routes_guide.md           # Quickstart endpoint documentation
├── updates.md                # Comprehensive record of changes from previous versions
└── overview.md               # Complete developer and architectural reference
```

---

## 3. In-Depth Module-by-Module Technical Guide

### A. `app/database.py` — Engine & Session Management

Manages database connectivity and per-request session lifecycles:

* **`DATABASE_URL`**: Loaded dynamically from `.env` using `python-dotenv`.
* **`create_engine(DATABASE_URL)`**: Instantiates the core database engine that manages the connection pool to PostgreSQL.
* **`SessionLocal`**: Configured session factory:
  ```python
  SessionLocal = sessionmaker(
      autocommit=False,
      autoflush=False,
      expire_on_commit=False,
      bind=engine
  )
  ```
  * `autocommit=False`: Ensures operations execute inside managed transactions that require explicit `db.commit()`.
  * `autoflush=False`: Avoids premature flushes before queries or object state mutations are finalized.
  * `expire_on_commit=False`: Prevents cached object attributes from expiring after commit, eliminating `DetachedInstanceError` during FastAPI response serialization.
* **`Base = declarative_base()`**: Base class for all ORM models.
* **`get_db()`**: FastAPI dependency generator that yields an isolated `SessionLocal` instance per request and guarantees `db.close()` inside a `finally` block.

---

### B. `app/models.py` — SQLAlchemy Relational Models

Defines the tables, foreign key constraints, cascade rules, and bidirectional relationships:

#### 1. Association Table: `student_subject`
Connects students and subjects in a Many-to-Many relationship:
* `student_id`: Integer, ForeignKey(`students.id`, `ondelete="CASCADE"`), Primary Key.
* `subject_id`: Integer, ForeignKey(`subjects.id`, `ondelete="CASCADE"`), Primary Key.

#### 2. `User` (`users` table)
Authentication entity representing credentials and system access:
* **Columns**:
  * `id`: Integer, Primary Key, indexed.
  * `username`: String, unique, indexed, nullable.
  * `email`: String, unique, indexed, non-nullable.
  * `hashed_password`: String, non-nullable.
  * `role`: String, non-nullable, default=`"student"`.
  * `is_active`: Boolean, non-nullable, default=`True`.
* **Relationships**:
  * `student_profile`: One-to-One to `Student` (`uselist=False`, `cascade="all, delete-orphan"`, `back_populates="user"`).
  * `teacher_profile`: One-to-One to `Teacher` (`uselist=False`, `cascade="all, delete-orphan"`, `back_populates="user"`).

#### 3. `Class` (`classes` table)
Classroom entity:
* **Columns**:
  * `id`: Integer, Primary Key, indexed.
  * `name`: String, unique, indexed, non-nullable.
  * `class_teacher_id`: Integer, ForeignKey(`teachers.id`, `ondelete="SET NULL"`), nullable.
* **Relationships**:
  * `students`: One-to-Many to `Student` (`back_populates="student_class"`).
  * `class_teacher`: One-to-One to `Teacher` (`back_populates="managed_class"`).

#### 4. `Teacher` (`teachers` table)
Instructor entity:
* **Columns**:
  * `id`: Integer, Primary Key, indexed.
  * `name`: String, non-nullable.
  * `email`: String, unique, indexed, non-nullable.
  * `user_id`: Integer, ForeignKey(`users.id`, `ondelete="CASCADE"`), unique, nullable.
* **Relationships**:
  * `user`: Many-to-One / One-to-One back-link to `User` (`back_populates="teacher_profile"`).
  * `managed_class`: One-to-One to `Class` (`back_populates="class_teacher"`, `uselist=False`).
  * `subjects`: One-to-Many to `Subject` (`back_populates="teacher"`).

#### 5. `Subject` (`subjects` table)
Curriculum subject entity:
* **Columns**:
  * `id`: Integer, Primary Key, indexed.
  * `name`: String, unique, indexed, non-nullable.
  * `teacher_id`: Integer, ForeignKey(`teachers.id`, `ondelete="SET NULL"`), nullable.
* **Relationships**:
  * `teacher`: Many-to-One to `Teacher` (`back_populates="subjects"`).
  * `students`: Many-to-Many to `Student` via `student_subject` (`back_populates="subjects"`).

#### 6. `Student` (`students` table)
Enrolled student entity:
* **Columns**:
  * `id`: Integer, Primary Key, indexed.
  * `name`: String, non-nullable.
  * `email`: String, unique, indexed, non-nullable.
  * `dob`: Date, nullable.
  * `phone_number`: String, nullable.
  * `class_id`: Integer, ForeignKey(`classes.id`, `ondelete="SET NULL"`), nullable.
  * `user_id`: Integer, ForeignKey(`users.id`, `ondelete="CASCADE"`), unique, nullable.
* **Relationships**:
  * `user`: Link back to `User` (`back_populates="student_profile"`).
  * `student_class`: Many-to-One to `Class` (`back_populates="students"`).
  * `subjects`: Many-to-Many to `Subject` via `student_subject` (`back_populates="students"`).

---

### C. `app/schemas.py` — Pydantic Validation & Serialization

Defines schemas for incoming request payloads and outgoing JSON responses:

#### Auth & User Schemas
* `UserBase`: Contains `email: EmailStr`.
* `UserSignup`: Extends `UserBase` with `name`, `password`, `role = "student"`, `class_id: Optional[int]`, `dob: Optional[date]`, `phone_number: Optional[str]`.
* `UserResponse`: Extends `UserBase` with `id: int`, `role: str`, `is_active: bool`. Configured with `from_attributes = True`.
* `Token`: Access token response schema with `access_token: str`, `token_type: str`.

#### Student Schemas
* `StudentBase`: `name: str`, `email: EmailStr`, `class_id: Optional[int]`, `dob: Optional[date]`, `phone_number: Optional[str]`.
* `StudentAdminCreate`: Extends `StudentBase` with mandatory `password: str` for administrator-driven account provisioning.
* `StudentUpdate`: Optional fields (`name`, `email`, `class_id`, `dob`, `phone_number`).
* `StudentResponse`: Extends `StudentBase` with `id: int`, `user_id: Optional[int]`. (`from_attributes = True`).

#### Teacher Schemas
* `TeacherBase`: `name: str`, `email: EmailStr`.
* `TeacherAdminCreate`: Extends `TeacherBase` with `password: str`.
* `TeacherUpdate`: Optional fields (`name`, `email`).
* `TeacherResponse`: Extends `TeacherBase` with `id: int`, `user_id: Optional[int]`. (`from_attributes = True`).

#### Subject Schemas
* `SubjectBase`: `name: str`, `teacher_id: Optional[int]`.
* `SubjectResponse`: Extends `SubjectBase` with `id: int`. (`from_attributes = True`).

---

### D. `app/auth.py` — Cryptography, Tokens & RBAC

Handles password hashing, token generation, user verification, and role access control:

* **Password Hashing & Verification**:
  ```python
  def verify_password(plain_password: str, hashed_password: str) -> bool:
      password_bytes = plain_password[:72].encode("utf-8")
      hashed_bytes = hashed_password.encode("utf-8")
      return bcrypt.checkpw(password_bytes, hashed_bytes)

  def get_password_hash(password: str) -> str:
      password_bytes = password[:72].encode("utf-8")
      salt = bcrypt.gensalt()
      return bcrypt.hashpw(password_bytes, salt).decode("utf-8")
  ```
  * Protects against bcrypt buffer overflow crashes by truncating input to 72 bytes explicitly before encoding.

* **JWT Generation (`create_access_token`)**:
  * Encodes payload (`sub` set to user's email, `role`) and sets UTC expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 30 min) signed with `SECRET_KEY` and `HS256`.

* **Current User Dependency (`get_current_user`)**:
  * Extracts Bearer token from `Authorization` header via `OAuth2PasswordBearer(tokenUrl="/auth/login")`.
  * Decodes token, validates signature, queries user by `email == payload["sub"]`, verifies `is_active is True`.

* **Role Guard Factory (`require_roles`)**:
  * Dynamic FastAPI dependency factory that restricts endpoints to authorized roles:
  ```python
  def require_roles(*allowed_roles: str):
      def role_checker(current_user: models.User = Depends(get_current_user)) -> models.User:
          if current_user.role not in allowed_roles:
              raise HTTPException(
                  status_code=status.HTTP_403_FORBIDDEN,
                  detail=f"Operation not permitted. Required role: {', '.join(allowed_roles)}",
              )
          return current_user
      return role_checker
  ```

---

### E. `app/crud.py` — Business Logic & Database Operations

Contains transaction handling and atomic entity-profile synchronization:

* **`register_user(db, user_data)`**:
  * Enforces public registration policy: only `role="student"` is permitted (HTTP 403 otherwise).
  * Validates email uniqueness across `users` table (HTTP 409 if duplicate).
  * Validates `class_id` if provided (HTTP 400 if class does not exist).
  * Creates `User` and `Student` records in a single database transaction, linking `Student.user_id` to `User.id` via `db.flush()`.
* **`create_student_with_account(db, student_data)`**:
  * Allows `admin` / `principal` to provision a student account with credentials and profile simultaneously.
* **`get_students(db, skip, limit)` / `get_student(db, student_id)`**:
  * Queries student records with offset pagination and primary key lookups.
* **`update_student(db, student_id, student_update)`**:
  * Updates student fields; if email is modified, validates uniqueness and automatically synchronizes the linked `user.email`.
* **`delete_student(db, student_id)`**:
  * Deletes the student profile and the associated `User` record cleanly in a single transaction.
* **`create_teacher_with_account(db, teacher_data)`**:
  * Allows `admin` / `principal` to provision a teacher account (`role="teacher"`) and corresponding `Teacher` profile record atomically.
* **`get_teachers(db, skip, limit)` / `get_teacher(db, teacher_id)`**:
  * Retrieves teacher records with pagination and single-entity lookups.
* **`update_teacher(db, teacher_id, teacher_update)`**:
  * Modifies teacher fields; synchronizes linked `user.email` upon email update.
* **`delete_teacher(db, teacher_id)`**:
  * Deletes teacher profile and corresponding `User` record.
* **`enroll_student_in_subject(db, student_id, subject_id, current_user)`**:
  * Checks student and subject existence (HTTP 404 if not found).
  * If caller is a `teacher`, enforces that the teacher is the designated instructor for that subject (`subject.teacher_id == teacher.id`, HTTP 403 otherwise).
  * Prevents duplicate enrollment (HTTP 400).
  * Appends subject to `student.subjects` relationship collection.
* **`unenroll_student_from_subject(db, student_id, subject_id, current_user)`**:
  * Enforces teacher ownership check, validates active enrollment, and removes subject from `student.subjects`.

---

### F. `app/main.py` — REST Endpoints & Route Definitions

Defines route paths, HTTP verbs, status codes, response schemas, and RBAC guards:

#### Summary of All Endpoints

| Category | Method | Endpoint | Allowed Roles | Description | Status Code |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/auth/signup` | Public | Register new student account & profile | `201 Created` |
| **Auth** | `POST` | `/auth/login` | Public | Authenticate and obtain JWT access token | `200 OK` |
| **Students** | `POST` | `/students/` | `admin`, `principal` | Create student account & profile | `201 Created` |
| **Students** | `GET` | `/students/` | `admin`, `principal`, `teacher` | List all students (paginated) | `200 OK` |
| **Students** | `GET` | `/students/{student_id}` | Authenticated (`get_current_user`) | Get single student details | `200 OK` |
| **Students** | `PUT` | `/students/{student_id}` | `admin`, `principal` | Update student profile and credentials | `200 OK` |
| **Students** | `DELETE`| `/students/{student_id}` | `admin`, `principal` | Delete student and linked user account | `204 No Content` |
| **Teachers** | `POST` | `/teachers/` | `admin`, `principal` | Create teacher account & profile | `201 Created` |
| **Teachers** | `GET` | `/teachers/` | `admin`, `principal` | List all teachers (paginated) | `200 OK` |
| **Teachers** | `GET` | `/teachers/{teacher_id}` | Authenticated (`get_current_user`) | Get single teacher details | `200 OK` |
| **Teachers** | `PUT` | `/teachers/{teacher_id}` | `admin`, `principal` | Update teacher profile and credentials | `200 OK` |
| **Teachers** | `DELETE`| `/teachers/{teacher_id}` | `admin`, `principal` | Delete teacher and linked user account | `204 No Content` |
| **Enrollment**| `POST` | `/students/{student_id}/subjects/{subject_id}/enroll` | `admin`, `principal`, `teacher` | Enroll student into a subject | `200 OK` |
| **Enrollment**| `POST` | `/students/{student_id}/subjects/{subject_id}/unenroll` | `admin`, `principal`, `teacher` | Remove student from a subject | `200 OK` |

---

### G. `app/seed_roles.py` — Database Seeding Script

An initialization utility that populates default administrative and instructor accounts:

* **Admin**: `email: "admin@school.com"`, `username: "admin"`, `password: "admin123"`, `role: "admin"`
* **Principal**: `email: "principal@school.com"`, `username: "principal"`, `password: "principal123"`, `role: "principal"`
* **Teacher**: `email: "teacher@school.com"`, `username: "teacher"`, `password: "teacher123"`, `role: "teacher"`, with linked `Teacher(name="Head Teacher", email="teacher@school.com")`.

To execute the seeder:
```bash
python -m app.seed_roles
```

---

## 4. End-to-End Request Lifecycles

### A. Authentication & Login Flow

```text
[ Client Request: POST /auth/login (username=email, password=***) ]
                             │
                             ▼
[ FastAPI OAuth2PasswordRequestForm receives form-data ]
                             │
                             ▼
[ DB Query: SELECT * FROM users WHERE email = ? LIMIT 1 ]
                             │
            ┌────────────────┴────────────────┐
       User Found                        User Not Found
            │                                 │
            ▼                                 ▼
[ auth.verify_password ]             [ HTTP 401 Unauthorized ]
   - Truncates to 72 bytes
   - bcrypt.checkpw
            │
      ┌─────┴─────┐
   Matches     Mismatch
      │           │
      ▼           ▼
[ Check Active ] [ HTTP 401 Unauthorized ]
      │
      ├─ is_active = False ──> [ HTTP 403 Forbidden ]
      │
      └─ is_active = True
              │
              ▼
[ auth.create_access_token ]
   - Claims: {"sub": user.email, "role": user.role, "exp": ...}
   - Signed with HS256
              │
              ▼
[ HTTP 200 OK: {"access_token": "...", "token_type": "bearer"} ]
```

---

### B. Student Registration & Dual-Entity Creation Flow

```text
[ Client Request: POST /auth/signup ]
Payload: { name, email, password, role="student", class_id, dob, phone_number }
                             │
                             ▼
[ Validation: user_data.role == "student" ] ──(No)──> [ HTTP 403 Forbidden ]
                             │ (Yes)
                             ▼
[ Check Existing User: email == user_data.email ] ──(Exists)──> [ HTTP 409 Conflict ]
                             │ (Available)
                             ▼
[ Validate Class (if class_id provided) ] ──(Invalid)──> [ HTTP 400 Bad Request ]
                             │ (Valid)
                             ▼
[ Database Transaction Begin ]
   1. user = User(username=email, email=email, hashed_password=hash(pwd), role="student")
   2. db.add(user)
   3. db.flush()  <── Generates user.id
   4. student = Student(user_id=user.id, name=name, email=email, class_id=class_id, ...)
   5. db.add(student)
   6. db.commit()
   7. db.refresh(user)
                             │
                             ▼
[ HTTP 201 Created: UserResponse(id, email, role, is_active) ]
```

---

### C. Subject Enrollment & Role Validation Flow

```text
[ Client Request: POST /students/{student_id}/subjects/{subject_id}/enroll ]
Header: Authorization: Bearer <token>
                             │
                             ▼
[ auth.require_roles("admin", "principal", "teacher") ]
   - Validates JWT signature & expiry
   - Checks caller role
                             │
                             ▼
[ Query Student & Subject ] ──(Either Missing)──> [ HTTP 404 Not Found ]
                             │
                             ▼
[ If Caller is "teacher" ]
   - teacher = db.query(Teacher).filter(user_id == current_user.id).first()
   - verify subject.teacher_id == teacher.id ──(Mismatch)──> [ HTTP 403 Forbidden ]
                             │
                             ▼
[ Check Duplicate Enrollment: subject in student.subjects ] ──(Duplicate)──> [ HTTP 400 Bad Request ]
                             │
                             ▼
[ student.subjects.append(subject) ]
[ db.commit() & db.refresh(student) ]
                             │
                             ▼
[ HTTP 200 OK: {"detail": "Student successfully enrolled in subject"} ]
```

---

## 5. Database Migrations with Alembic

The database schema evolution is tracked linearly in the `alembic/versions/` directory:

### Linear Migration Chain

```text
[ 8944d7db6b33 ] (Initial: Create students table with id, name, email, department)
        │
        ▼
[ 232068afd9e1 ] (Add dob and phone_number columns to students)
        │
        ▼
[ c1881ecb9503 ] (Create classes, teachers, subjects, and student_subjects; add class_id to students)
        │
        ▼
[ 21d66fd12994 ] (Add class_teacher_id foreign key constraint to classes)
        │
        ▼
[ a22fb04d03dd ] (Add users table with username, email, hashed_password, is_active) [HEAD]
```

### Key Alembic Commands

* **Apply all pending migrations to database**:
  ```bash
  alembic upgrade head
  ```
* **Rollback the most recent migration**:
  ```bash
  alembic downgrade -1
  ```
* **View current revision in database**:
  ```bash
  alembic current
  ```
* **Inspect linear migration history**:
  ```bash
  alembic history --verbose
  ```

---

## 6. SQL Compilation & Query Translation

SQLAlchemy 2.0 compiles Python ORM expressions into dialect-specific PostgreSQL queries:

| Python Operation | Compiled PostgreSQL Statement |
| :--- | :--- |
| `db.query(models.Student).offset(0).limit(100).all()` | `SELECT id, name, email, dob, phone_number, class_id, user_id FROM students OFFSET 0 LIMIT 100;` |
| `db.query(models.User).filter(models.User.email == email).first()` | `SELECT id, username, email, hashed_password, role, is_active FROM users WHERE email = %(email_1)s LIMIT 1;` |
| `db.query(models.Teacher).filter(models.Teacher.id == teacher_id).first()` | `SELECT id, name, email, user_id FROM teachers WHERE id = %(id_1)s LIMIT 1;` |
| `student.subjects.append(subject)` | `INSERT INTO student_subject (student_id, subject_id) VALUES (%(student_id)s, %(subject_id)s);` |
| `student.subjects.remove(subject)` | `DELETE FROM student_subject WHERE student_id = %(student_id)s AND subject_id = %(subject_id)s;` |
| `db.delete(student.user)` | `DELETE FROM users WHERE id = %(id_1)s;` *(Cascades to delete linked student record)* |

---

## 7. Security Best Practices & Design Decisions

1. **Bcrypt 72-Byte Boundary Protection**:
   * Bcrypt natively truncates or errors on inputs exceeding 72 bytes. The auth helper explicitly applies `[:72].encode("utf-8")` to guarantee stability and prevent Denial of Service (DoS) through unbounded password lengths.
2. **Coupled Account-Profile Lifecycle**:
   * Creating a student or teacher automatically creates their authentication `User` entity.
   * Deleting a student or teacher deletes the underlying `User` record to prevent orphaned authentication records.
   * Updating a student or teacher's email synchronizes `User.email` in lockstep.
3. **Strict RBAC Separation**:
   * Route dependencies (`auth.require_roles`) isolate administrative capabilities from instructors and learners.
   * Subject enrollments verify teacher ownership, ensuring instructors can only enroll students in their assigned subjects.
4. **Session Lifecycle Guarantees**:
   * `expire_on_commit=False` prevents lazy loading detachment errors across asynchronous and dependency boundaries in FastAPI.
