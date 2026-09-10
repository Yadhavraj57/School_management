# School Management API — Codebase Issues

This document records the key issues found during a review of the FastAPI school management backend. The application imports successfully, but it is not production-ready. The main blockers are database schema drift, authorization gaps, incomplete APIs, and weak operational safeguards.

## Critical issues

### 1. Database migrations and ORM models are out of sync

The original migrations do not create several fields and tables expected by `app/models.py`, including:

- `users.role`
- `students.user_id`
- `teachers.user_id`
- The `student_subject` association table (the old migration calls it `student_subjects`)

This caused the seed command to fail with:

```text
column users.role does not exist
```

An uncommitted alignment migration currently exists at `alembic/versions/f4d3c2b1a090_align_schema_with_current_models.py`, but it requires review before it is used on a populated database.

### 2. Students can read any student's private information

Any authenticated user can call `GET /students/{student_id}`. There is no ownership check, so a student can enumerate IDs and retrieve other students' names, email addresses, dates of birth, and phone numbers.

Relevant code: `app/main.py`, `read_student()`.

### 3. Any authenticated user can read any teacher

`GET /teachers/{teacher_id}` has the same broken object-level authorization issue. Authentication is required, but the user's role or ownership is not checked.

Relevant code: `app/main.py`, `read_teacher()`.

### 4. The application accepts a fixed fallback JWT secret

If `SECRET_KEY` is absent, the application uses:

```text
fallback_secret_change_me
```

Anyone who knows the source code could use this value to forge tokens. The application should refuse to start unless a strong secret has been explicitly configured.

Relevant code: `app/auth.py`.

### 5. Password handling is incorrect

Passwords are truncated by characters instead of UTF-8 bytes. Testing confirmed that:

- Some Unicode passwords raise `ValueError` during hashing because they exceed bcrypt's 72-byte limit.
- Two different long ASCII passwords with the same first 72 characters are treated as the same password.

Passwords should be validated by byte length or hashed using a modern password scheme without silent truncation.

Relevant code: `app/auth.py`, `get_password_hash()` and `verify_password()`.

## High-priority issues

### 6. Core APIs are missing

The application has no endpoints for:

- Creating or managing classes
- Creating or managing subjects
- User administration
- Viewing the current authenticated user

Subject enrollment cannot be used through a normal API workflow because subjects cannot be created through the API.

### 7. The documentation describes endpoints that do not exist

`routes_guide.md` documents routes such as:

- `/auth/signin`
- `/auth/me`
- `/users`
- `/classes`
- `/subjects`

These routes are not registered in `app/main.py`. The actual login endpoint is `/auth/login`.

### 8. Seeded credentials are hardcoded and insecure

The seed script contains predictable development credentials:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@school.com` | `admin123` |
| Principal | `principal@school.com` | `principal123` |
| Teacher | `teacher@school.com` | `teacher123` |

These accounts must never be created with these passwords in production.

Relevant code: `app/seed_roles.py`.

### 9. The seed script hides failures

The script catches every exception, prints an error, and exits with a successful status code. CI, deployment scripts, or developers can therefore believe seeding succeeded even when no rows were inserted.

Relevant code: `app/seed_roles.py`, `seed_data()`.

### 10. The seed script is only partially idempotent

If the teacher user exists but its teacher profile is missing, running the seed script again will not create the missing profile.

### 11. Alembic downgrades are broken

A static PostgreSQL downgrade test failed because older migrations attempt to drop unnamed constraints:

```text
CompileError: Can't emit DROP CONSTRAINT ... it has no name
```

Relevant code: `alembic/versions/21d66fd12994_add_class_teacher_to_class.py` and other migrations that use `drop_constraint(None, ...)`.

### 12. The alignment migration is unsafe for populated databases

The current uncommitted alignment migration drops legacy columns and changes nullability without a complete data migration strategy. This may be acceptable for confirmed-empty tables, but it could destroy data or fail when applied to an existing populated deployment.

Relevant code: `alembic/versions/f4d3c2b1a090_align_schema_with_current_models.py`.

## Validation and reliability issues

### 13. Input validation is too weak

The request schemas do not adequately validate:

- Password length or strength
- Empty names
- Phone-number format
- Future dates of birth
- Allowed role values

Roles should use a constrained enum rather than arbitrary strings.

Relevant code: `app/schemas.py`.

### 14. Update schemas allow invalid null values

Fields such as `name` and `email` can explicitly be set to `null`, even though the corresponding database columns are non-nullable. This produces a database exception instead of a clear request-validation error.

Relevant code: `StudentUpdate` and `TeacherUpdate` in `app/schemas.py`.

### 15. Database internals are exposed to API clients

Several CRUD functions return raw `IntegrityError` text. These messages can expose database table names, constraints, and SQL implementation details.

Relevant code: `app/crud.py`.

### 16. Email updates leave usernames stale

New users receive the email address as their username. Student and teacher email updates change the profile email and `User.email`, but do not update `User.username`.

Relevant code: `update_student()` and `update_teacher()` in `app/crud.py`.

### 17. Pagination is unbounded

The `skip` and `limit` parameters accept negative or extremely large values. A caller can request excessive numbers of records.

Relevant code: `read_students()` and `read_teachers()` in `app/main.py`.

### 18. Configuration is not validated

`DATABASE_URL` is read directly from the environment, and the SQLAlchemy engine is created during module import. There is no validated settings object, clear missing-configuration error, or separation between development and production settings.

Relevant code: `app/database.py`.

### 19. `.env.example` is empty

The example environment file does not document required PostgreSQL or JWT settings. At minimum, it should describe:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/database_name
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 20. There are no automated tests or CI

The repository contains no unit tests, integration tests, authorization tests, migration tests, or CI workflow. Security regressions and migration problems can therefore go undetected.

### 21. Dependency versions are not reproducibly pinned

Dependencies have minimum versions only, and the repository has no lock file. A future major package release could silently break installation or runtime behavior.

## Additional operational gaps

The application also lacks:

- Login rate limiting or brute-force protection
- Token revocation or refresh-token support
- Security and audit logging
- Health/readiness endpoints
- CORS configuration for browser frontends
- Database connection health handling such as pool pre-ping
- A documented production deployment process

## Review checks performed

- Python source compilation succeeded.
- Application import and route generation succeeded with the current environment.
- Installed Python dependencies passed `pip check`.
- Alembic upgrade SQL generation succeeded.
- Alembic downgrade SQL generation failed on unnamed constraints.
- Password tests confirmed Unicode byte-length failure and long-password truncation collisions.
- No automated tests, CI configuration, or dependency lock file were found.
