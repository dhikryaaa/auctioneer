"""
Seeder for the auth service.

Inserts 2 admins and 5 regular users with bcrypt-hashed passwords.
Idempotent: checks each email first, so running it twice won't error
on the unique-email constraint.

Run from /services/auth (venv active, AFTER migrations have been applied):
    python seed.py
"""
import asyncio
from sqlalchemy import select

from database import SessionLocal
from models import User
from security import hash_password


# (name, email, password, role)
SEED_USERS = [
    # ---- admins ----
    ("Admin One", "admin1@gmail.com", "Admin@123", "admin"),
    ("Admin Two", "admin2@gmail.com", "Admin@123", "admin"),
    # ---- regular users ----
    ("User One",   "user1@gmail.com", "User@123", "user"),
    ("User Two",   "user2@gmail.com", "User@123", "user"),
    ("User Three", "user3@gmail.com", "User@123", "user"),
    ("User Four",  "user4@gmail.com", "User@123", "user"),
    ("User Five",  "user5@gmail.com", "User@123", "user"),
]


async def seed() -> None:
    async with SessionLocal() as session:
        created, skipped = 0, 0
        for name, email, password, role in SEED_USERS:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            existing = result.scalars().first()

            if existing:
                skipped += 1
                print(f"  skip   {email} (already exists)")
                continue

            session.add(User(
                name=name,
                email=email,
                password_hash=hash_password(password),
                role=role,
            ))
            created += 1
            print(f"  create {email} ({role})")

        await session.commit()
        print(f"\nDone. created={created}, skipped={skipped}")


if __name__ == "__main__":
    asyncio.run(seed())