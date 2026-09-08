# School Management API: Simplified Routes & Quickstart Guide

Welcome to the **Student & School Management API**! 

This guide explains what the application does in simple terms, breaks down the 4 user roles, and lists every available route with examples of what to send and what to expect in response.

---

## 1. What is this Application?

This is a complete backend web service built with **FastAPI** and **PostgreSQL** that lets a school manage:

1. **Classes** (classrooms like Standard 10-A, 11-B)
2. **Teachers** (faculty instructors)
3. **Subjects** (courses like Physics, Math, Chemistry)
4. **Students** (enrolled learners)
5. **Subject Enrollments** (assigning students to courses)
6. **User Accounts & Authentication** (secure login with passwords and JWT tokens)
7. **Role-Based Access Control (RBAC)** (different permissions for Admins, Principals, Teachers, and Students)

---

## 2. The 4 Roles Explained Simply

The application has 4 user levels:

* 👑 **`admin` (Superuser)**  
  Has full access to everything in the school. Admins are the **only** ones who can change user roles, promote principals, or delete user accounts.

* 🏫 **`principal` (School Head)**  
  Manages daily school operations: creates, updates, and deletes Classes, Teachers, Subjects, and Students.  
  *Safety Guard*: Principals **cannot** change user roles and **cannot** edit or delete Admin accounts.

* 🧑‍🏫 **`teacher` (Instructor)**  
  Can view Classes, Subjects, and Students. Can enroll or unenroll students into the subjects they teach. Can update their own phone number and profile.

* 🎓 **`student` (Learner)**  
  Can view their own profile, see which class they are assigned to, and check which subjects they are enrolled in. They cannot modify school records.

---

## 3. Quick Start: How to Run and Test the API

### Step 1: Start the Server

Open your terminal, navigate to the folder, and run:

```bash
uvicorn app.main:app --reload
```

### Step 2: Open Interactive Documentation (Swagger UI)

Open your web browser and go to:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

This gives you a visual web interface where you can test any route by clicking **"Try it out"**.

### Step 3: Log in to Get Your Access Token

1. In Swagger UI, find the **`POST /auth/signin`** endpoint.
2. Enter the default administrator credentials:
   * **Username**: `superadmin`
   * **Password**: `AdminPass@123`
3. Click **Execute**. You will receive an `access_token`.
4. Scroll to the top of the page, click the green **Authorize 🔓** button, paste the token, and click **Authorize**.
5. You are now logged in as `admin` and can test all protected routes!

*(To test as Principal, log in with `username: "school_principal"` and `password: "PrincipalPass@123"`)*

---

## 4. Complete Route-by-Route Reference

Here is every single route available in the application:

---

### A. Authentication Routes

These routes handle signing up, logging in, and checking who is currently logged in.

---

#### 1. Public Signup
* **Method**: `POST`
* **URL**: `/auth/signup`
* **Access**: Public (Anyone can call this)
* **What it does**: Registers a new user account. If you choose `role="student"`, it **automatically creates a Student record**. If you choose `role="teacher"`, it **automatically creates a Teacher record**.
* **Safety Rule**: You **cannot** sign up as `admin` or `principal`. Those roles must be assigned by an Admin.
* **Request Body Example (Student Signup)**:
  ```json
  {
    "username": "rahul_sharma",
    "email": "rahul.sharma@student.edu",
    "password": "MySecretPassword123",
    "role": "student",
    "full_name": "Rahul Sharma",
    "department": "Computer Science",
    "dob": "2006-03-15",
    "phone_number": "9876543210",
    "class_id": 10
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "id": 12,
    "username": "rahul_sharma",
    "email": "rahul.sharma@student.edu",
    "role": "student",
    "is_active": true
  }
  ```

---

#### 2. Sign In (Login)
* **Method**: `POST`
* **URL**: `/auth/signin`
* **Access**: Public
* **What it does**: Verifies username and password and returns a secure JWT access token.
* **Request Body (Form Data)**:
  * `username`: `superadmin`
  * `password`: `AdminPass@123`
* **Success Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "role": "admin"
  }
  ```

---

#### 3. View Current Logged-in Profile
* **Method**: `GET`
* **URL**: `/auth/me`
* **Access**: Any logged-in user (`admin`, `principal`, `teacher`, `student`)
* **What it does**: Checks your JWT token and tells you your user details and active role.
* **Success Response (200 OK)**:
  ```json
  {
    "id": 1,
    "username": "superadmin",
    "email": "superadmin@school.edu",
    "role": "admin",
    "is_active": true
  }
  ```

---

### B. User Management Routes

These routes allow administrative management of login accounts.

---

#### 1. List All Users
* **Method**: `GET`
* **URL**: `/users/`
* **Access**: `admin`, `principal`
* **What it does**: Returns a list of all registered accounts (students, teachers, principals, admins).

---

#### 2. Get User by ID
* **Method**: `GET`
* **URL**: `/users/{user_id}`
* **Access**: `admin`, `principal`
* **What it does**: Returns details of a specific user ID.

---

#### 3. Update User
* **Method**: `PUT`
* **URL**: `/users/{user_id}`
* **Access**: `admin`, `principal`
* **Safety Guards**:
  * **Principals CANNOT change user roles.** (Only Admins can).
  * **Principals CANNOT edit Admin accounts.**
  * **Principals CANNOT edit other Principal accounts.**
* **Request Body Example**:
  ```json
  {
    "email": "new.email@school.edu",
    "is_active": true
  }
  ```

---

#### 4. Delete User
* **Method**: `DELETE`
* **URL**: `/users/{user_id}`
* **Access**: `admin` only
* **What it does**: Deletes a user account. Admins cannot delete their own active account.

---

### C. Class Management Routes

These routes manage classrooms (e.g., Standard 9-A).

---

#### 1. Create Class
* **Method**: `POST`
* **URL**: `/classes/`
* **Access**: `admin`, `principal`
* **Request Body Example**:
  ```json
  {
    "name": "Standard 10-B",
    "section": "B",
    "class_teacher_id": 5
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "id": 15,
    "name": "Standard 10-B",
    "section": "B",
    "class_teacher_id": 5
  }
  ```

---

#### 2. List All Classes
* **Method**: `GET`
* **URL**: `/classes/`
* **Access**: Anyone logged in

---

#### 3. Get Single Class
* **Method**: `GET`
* **URL**: `/classes/{class_id}`
* **Access**: Anyone logged in

---

#### 4. Update Class
* **Method**: `PUT`
* **URL**: `/classes/{class_id}`
* **Access**: `admin`, `principal`
* **Request Body Example**:
  ```json
  {
    "section": "B+"
  }
  ```

---

#### 5. Delete Class
* **Method**: `DELETE`
* **URL**: `/classes/{class_id}`
* **Access**: `admin`, `principal`
* **What it does**: Deletes the class. Any students in this class have their `class_id` safely set to `null` (they are not deleted).

---

### D. Teacher Management Routes

These routes manage instructors.

---

#### 1. Create Teacher
* **Method**: `POST`
* **URL**: `/teachers/`
* **Access**: `admin`, `principal`
* **Request Body Example**:
  ```json
  {
    "name": "Prof. Alan Turing",
    "email": "alan.turing@school.edu",
    "phone_number": "9876543219"
  }
  ```

---

#### 2. List All Teachers
* **Method**: `GET`
* **URL**: `/teachers/`
* **Access**: Anyone logged in
* **What it does**: Returns all teachers along with the list of subjects they teach.

---

#### 3. Get Single Teacher
* **Method**: `GET`
* **URL**: `/teachers/{teacher_id}`
* **Access**: Anyone logged in

---

#### 4. Update Teacher
* **Method**: `PUT`
* **URL**: `/teachers/{teacher_id}`
* **Access**: `admin`, `principal`

---

#### 5. Delete Teacher
* **Method**: `DELETE`
* **URL**: `/teachers/{teacher_id}`
* **Access**: `admin`, `principal`
* **What it does**: Deletes the teacher. Any subjects they taught will have `teacher_id` set to `null`.

---

### E. Subject Management Routes

These routes manage courses/subjects offered in the school.

---

#### 1. Create Subject
* **Method**: `POST`
* **URL**: `/subjects/`
* **Access**: `admin`, `principal`
* **Request Body Example**:
  ```json
  {
    "name": "Artificial Intelligence",
    "code": "AI401",
    "teacher_id": 5
  }
  ```

---

#### 2. List All Subjects
* **Method**: `GET`
* **URL**: `/subjects/`
* **Access**: Anyone logged in

---

#### 3. Get Single Subject
* **Method**: `GET`
* **URL**: `/subjects/{subject_id}`
* **Access**: Anyone logged in

---

#### 4. Update Subject
* **Method**: `PUT`
* **URL**: `/subjects/{subject_id}`
* **Access**: `admin`, `principal`

---

#### 5. Delete Subject
* **Method**: `DELETE`
* **URL**: `/subjects/{subject_id}`
* **Access**: `admin`, `principal`
* **What it does**: Deletes the subject and automatically removes it from any enrolled students' records.

---

### F. Student Management Routes

These routes manage students.

---

#### 1. Create Student Directly
* **Method**: `POST`
* **URL**: `/students/`
* **Access**: `admin`, `principal`
* **Request Body Example**:
  ```json
  {
    "name": "Pooja Hegde",
    "email": "pooja.hegde@student.edu",
    "department": "Science",
    "dob": "2006-09-12",
    "phone_number": "9123456799",
    "class_id": 10
  }
  ```

---

#### 2. List All Students
* **Method**: `GET`
* **URL**: `/students/`
* **Access**: Anyone logged in
* **What it does**: Returns all students with their assigned classroom and enrolled subjects.

---

#### 3. Get Single Student
* **Method**: `GET`
* **URL**: `/students/{student_id}`
* **Access**: Anyone logged in

---

#### 4. Update Student
* **Method**: `PUT`
* **URL**: `/students/{student_id}`
* **Access**: `admin`, `principal`

---

#### 5. Delete Student
* **Method**: `DELETE`
* **URL**: `/students/{student_id}`
* **Access**: `admin`, `principal`
* **What it does**: Deletes the student and removes all their subject enrollments.

---

### G. Enrollment & Unenrollment Routes

These routes enroll or drop students from courses.

---

#### 1. Enroll Student in a Subject
* **Method**: `POST`
* **URL**: `/students/{student_id}/enroll/{subject_id}`
* **Access**: `admin`, `principal`, `teacher`
* **What it does**: Adds the subject to the student's enrolled courses list.
* **Success Response (200 OK)**: Returns the updated student profile with the new subject added to `subjects`.

---

#### 2. Unenroll Student from a Subject
* **Method**: `DELETE`
* **URL**: `/students/{student_id}/unenroll/{subject_id}`
* **Access**: `admin`, `principal`, `teacher`
* **What it does**: Drops the student from that course.
* **Success Response (200 OK)**: Returns the student profile with that subject removed.

---

## 5. Summary of Error Codes You Might See

| HTTP Status Code | What it Means | How to Fix It |
| :--- | :--- | :--- |
| **`400 Bad Request`** | Duplicate data or invalid action | Check if the username, email, class name, or subject code already exists. |
| **`401 Unauthorized`** | Missing or invalid token | Log in via `/auth/signin` and copy the access token into the green Authorize button. |
| **`403 Forbidden`** | Your role is not allowed | For example, a student trying to delete a class, or a principal trying to change user roles. Log in as `admin`. |
| **`404 Not Found`** | The ID does not exist | Check if the student ID, class ID, or subject ID exists in the database. |
