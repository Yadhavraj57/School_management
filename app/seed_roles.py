from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.auth import get_password_hash


def seed_data():
    db: Session = SessionLocal()
    try:
        # 1. Admin User
        admin_email = "admin@school.com"
        admin_user = db.query(models.User).filter(models.User.email == admin_email).first()
        if not admin_user:
            admin_user = models.User(
                username="admin",
                email=admin_email,
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True,
            )
            db.add(admin_user)

        # 2. Principal User
        principal_email = "principal@school.com"
        principal_user = db.query(models.User).filter(models.User.email == principal_email).first()
        if not principal_user:
            principal_user = models.User(
                username="principal",
                email=principal_email,
                hashed_password=get_password_hash("principal123"),
                role="principal",
                is_active=True,
            )
            db.add(principal_user)

        # 3. Teacher User & Profile
        teacher_email = "teacher@school.com"
        teacher_user = db.query(models.User).filter(models.User.email == teacher_email).first()
        if not teacher_user:
            teacher_user = models.User(
                username="teacher",
                email=teacher_email,
                hashed_password=get_password_hash("teacher123"),
                role="teacher",
                is_active=True,
            )
            db.add(teacher_user)
            db.flush()

            teacher_profile = models.Teacher(
                user_id=teacher_user.id,
                name="Head Teacher",
                email=teacher_email,
            )
            db.add(teacher_profile)

        db.commit()
        print("Initial users and roles seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()