# Student & School Management API: Changelog & Updates Reference

This document provides a comprehensive log of all updates, architectural refinements, schema alignments, and security enhancements implemented in the current codebase compared to previous iterations.

---

## 1. Executive Summary of Changes

The codebase has evolved from a standalone single-entity CRUD prototype into an enterprise-ready, role-secured school management service. The latest iteration focuses on **strict synchronization between authentication accounts and role profiles**, **hardened password cryptography**, **standardized OAuth2 endpoints**, and **robust transaction management**.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              EVOLUTION ROADMAP                               │
├───────────────────┬──────────────────────────────────────────────────────────┤
│ Version 1 (Ver1)  │ Single `students` table, basic CRUD, no authentication.  │
├───────────────────┼──────────────────────────────────────────────────────────┤
│ Version 2 (Ver2)  │ Expanded schema with Classes, Teachers, Subjects, M:N    │
│                   │ enrollment table, and initial Alembic migrations.        │
├───────────────────┼──────────────────────────────────────────────────────────┤
│ Version 3 (Ver3)  │ Introduction of `users` table, JWT Bearer tokens, and     │
│                   │ multi-role RBAC (`admin`, `principal`, `teacher`, `student`).│
├───────────────────┼──────────────────────────────────────────────────────────┤
│ Version 4 / Current│ Atomic account-profile lifecycle synchronization, direct │
│ (Active Codebase) │ bcrypt 72-byte safe hashing, standardized /auth/login    │
│                   │ endpoint, teacher subject ownership checks, and          │
│                   │ expire_on_commit=False session stability.                │
└───────────────────┴──────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Breakdown of Updates

### A. Authentication & Security Hardening

| Feature / Area | Previous Implementation | Current Implementation | Rationale & Benefit |
| :--- | :--- | :--- | :--- |
| **Token Login Route** | Used `/auth/signin` non-standard endpoint name. | Standardized to `/auth/login` matching `OAuth2PasswordBearer(tokenUrl="/auth/login")`. | Fixes Swagger UI interactive authorization and complies with OpenAPI / OAuth2 specifications. |
| **Password Cryptography** | Relied on `passlib` wrapper around bcrypt without explicit input truncation. | Direct `bcrypt.hashpw` and `bcrypt.checkpw` with explicit `[:72].encode("utf-8")` slicing. | Eliminates unhandled `ValueError` exceptions caused by inputs exceeding bcrypt's 72-byte buffer limit. |
| **Public Signup Guard** | Signup allowed unvalidated role selection or lacked strict student-only enforcement. | `POST /auth/signup` strictly requires `role == "student"`, rejecting `admin` or `principal` signups with `403 Forbidden`. | Prevents privilege escalation and unauthorized creation of administrative accounts. |
| **Login Identifier** | Ambiguous username vs email handling. | Form data `username` explicitly maps to user's `email` for lookup and JWT `sub` claim. | Ensures consistent identity resolution and prevents username-email collisions. |

---

### B. Dual-Entity Account & Profile Lifecycle Synchronization

In previous versions, `User` login accounts and domain profiles (`Student`, `Teacher`) were loosely coupled, which could lead to orphaned accounts or inconsistent state. The current codebase enforces atomic synchronization:

1. **Atomic Student Registration**:
   * Calling `POST /auth/signup` creates the `User` record (with `role="student"`), calls `db.flush()` to obtain `user.id`, and creates the linked `Student` record within the **same transaction**.
2. **Admin-Driven Account Provisioning**:
   * `POST /students/` accepts `StudentAdminCreate` (including `password`), simultaneously provisioning the `User` login credentials and `Student` profile.
   * `POST /teachers/` accepts `TeacherAdminCreate` (including `password`), simultaneously provisioning the `User` credentials (role="teacher") and `Teacher` profile.
3. **Synchronized Email Updates**:
   * Modifying a student's or teacher's email via `PUT /students/{id}` or `PUT /teachers/{id}` automatically checks for collision across `users` and updates `User.email` in lockstep.
4. **Cascaded Account Deletion**:
   * Deleting a student via `DELETE /students/{id}` or teacher via `DELETE /teachers/{id}` explicitly deletes `student.user` / `teacher.user`, completely removing authentication credentials and preventing orphaned user records.

---

### C. Data Models & Schema Harmonization

| Entity | Previous State | Current State | Notes |
| :--- | :--- | :--- | :--- |
| **Association Table** | Referenced as `student_subjects` in documentation. | Defined as `student_subject` table in `app/models.py` with `secondary=student_subject`. | Fully aligned model definition with table registry. |
| **`User` Model** | `username` was required in early migrations. | `username` is nullable (`nullable=True`), `email` is primary unique identifier. | Streamlines authentication workflows using email. |
| **`Student` Model** | Contained legacy `department` field in early migration. | Cleaned up model to `id`, `name`, `email`, `dob`, `phone_number`, `class_id`, `user_id`. | Removes unused fields and maintains foreign key constraints. |
| **`Teacher` Model** | Loose relationship mapping. | Explicit `user_id` FK (unique), `managed_class` (1:1 with `Class`), and `subjects` (1:M with `Subject`). | Ensures clean bidirectional navigation across ORM entities. |
| **Cascade Behavior** | Missing explicit ORM cascade options. | Added `cascade="all, delete-orphan"` on `User.student_profile` and `User.teacher_profile`. | Ensures orphaned child profiles are cleaned up on user operations. |

---

### D. Endpoint & Route Signature Refinements

| Route | Previous Signature | Current Signature | Access Control |
| :--- | :--- | :--- | :--- |
| **Subject Enrollment** | `POST /students/{id}/enroll/{subject_id}` | `POST /students/{id}/subjects/{subject_id}/enroll` | `admin`, `principal`, `teacher` |
| **Subject Unenrollment**| `DELETE /students/{id}/unenroll/{subject_id}` | `POST /students/{id}/subjects/{subject_id}/unenroll` | `admin`, `principal`, `teacher` |
| **Teacher Enrollment Ownership** | Any teacher could enroll any student in any subject. | Enforced check: `subject.teacher_id == current_teacher.id`. | Teachers can only enroll/unenroll students in courses they personally teach. |
| **Student Listing** | Limited role filtering. | `GET /students/` accessible to `admin`, `principal`, and `teacher`. | Allows instructors to view student rosters. |
| **Teacher Listing** | Open to all authenticated users. | `GET /teachers/` restricted to `admin` and `principal`. | Protects faculty administrative data. |

---

### E. Database Session & Engine Stability

* **`expire_on_commit=False` Configured**:
  * In `app/database.py`, `SessionLocal` explicitly configures `expire_on_commit=False`.
  * **Issue Fixed**: Previously, committing a transaction expired instance attributes in memory. When FastAPI serialized related models (e.g. `classroom` or `subjects`) after the session closed, SQLAlchemy threw `DetachedInstanceError`.
  * **Outcome**: Attributes remain accessible in Python memory for clean Pydantic response formatting.

---

### F. Database Seeding Script (`app/seed_roles.py`)

* **Previous**: Basic seeder with placeholder passwords or mismatched accounts.
* **Current**:
  * Seeds `admin@school.com` (`username: "admin"`, role: `"admin"`).
  * Seeds `principal@school.com` (`username: "principal"`, role: `"principal"`).
  * Seeds `teacher@school.com` (`username: "teacher"`, role: `"teacher"`) with associated `Teacher` profile (`name: "Head Teacher"`).
  * Uses hashed passwords (`admin123`, `principal123`, `teacher123`) generated via `get_password_hash`.

---

## 3. Migration History Summary

The Alembic migration chain remains intact and tracks every step of database development:

1. `8944d7db6b33`: Initial `students` table creation.
2. `232068afd9e1`: Added `dob` and `phone_number` columns to `students`.
3. `c1881ecb9503`: Added `classes`, `teachers`, `subjects`, and `student_subjects` tables; added `class_id` FK to `students`.
4. `21d66fd12994`: Added `class_teacher_id` unique foreign key to `classes`.
5. `a22fb04d03dd`: Added `users` table (`username`, `email`, `hashed_password`, `is_active`).

---

## 4. Summary Table of Key Differences

| Dimension | Previous State | Current State |
| :--- | :--- | :--- |
| **Documentation File** | `overview.md` described generic or outdated endpoints (`/auth/signin`, `/classes/` CRUD, unmapped columns). | `overview.md` reflects exact current code, models, schemas, and routes without obsolete references. |
| **Changelog Separation** | Previous history was mixed or undocumented. | Dedicated `updates.md` cleanly separates version history from the technical overview. |
| **User-Profile Coupling** | Independent tables; potential orphan records. | Fully synchronized dual-entity transactions for both Students and Teachers. |
| **Password Security** | Standard passlib without byte truncation. | Direct Bcrypt with strict 72-byte UTF-8 truncation. |
| **Session Configuration** | Default sessionmaker. | `expire_on_commit=False` avoiding detached instance errors. |
| **Enrollment Endpoints** | Inconsistent URI parameters. | RESTful nested subject enrollment routes with instructor ownership validation. |
