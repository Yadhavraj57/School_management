# 🏫 School Management System

A comprehensive School Management System designed to manage student records, teacher details, classes, and administrative tasks efficiently.

---

## 📌 Features

- **Student Management:** Add, update, view, and remove student profiles and admission details.
- **Teacher & Staff Management:** Maintain records of faculty, subjects assigned, and contact information.
- **Course / Class Allocation:** Organize classes, sections, and subject assignments.
- **Attendance & Records:** Track attendance and manage academic performance.
- **Database Persistence:** Securely store and query school data with relational database integration.

---

## 🛠️ Tech Stack

- **Language:** Python
- **Framework:**  FastApi
- **Database:** * PostgreSQL 
- **Version Control:** Git & GitHub

---
## 📂 Project Structure

School_management/
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── app/
│   ├── __init__.py
│   ├── auth.py
│   ├── crud.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── seed_roles.py
├── .env.example
├── .gitignore
├── alembic.ini
├── overview.md
├── README.md
├── requirements.txt
├── routes_guide.md
└── updates.md

## 🚀 How to Run the Project

### 1. Clone the Repository
```bash
git clone [https://github.com/Yadhavraj57/School_management.git](https://github.com/Yadhavraj57/School_management.git)
cd School_management

#Create and Activate Virtual Environment
windows (Command Prompt / PowerShell):
python -m venv .venv
.venv\Scripts\activate

MacOS/Linux:
python3 -m venv .venv
source .venv/bin/activate

#Install Dependencies
pip install -r requirements.txt

#Configure Environment Variables
Windows:(PowerShell)
copy .env.example .env

macOS / Linux (Bash):
cp .env.example .env

Open .env to configure your database connection string and secret keys if required.

(Bash)
alembic upgrade head

#Seed Initial Roles (Optional)
Bash
python -m app.seed_roles

#Start the FastAPI Server
Bash
uvicorn app.main:app --reload