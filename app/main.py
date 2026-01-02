from fastapi import FastAPI
from . database import SessionLocal, engine,get_db
from . import models
from . routers import users,auth,categories
from . config import settings
from sqlalchemy.orm import Session
from . utils import hash_pass

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


app.include_router(users.router)
app.include_router(auth.router)
app.include_router(categories.router)

ADMIN_EMAIL = settings.ADMIN_EMAIL
ADMIN_PASSWORD = settings.ADMIN_PASSWORD

@app.on_event("startup")
def create_initial_admin():
    db: Session = SessionLocal()
    try:
        admin = db.query(models.User).filter(
            models.User.role == models.UserRole.admin
        ).first()

        if not ADMIN_EMAIL or not ADMIN_PASSWORD:
            print("ADMIN_EMAIL or ADMIN_PASSWORD not set. Admin creation skipped.")
            return
        hashed_password = hash_pass(ADMIN_PASSWORD)

        new_admin = models.User(
            name="Admin",
            email=ADMIN_EMAIL,
            hashed_password=hashed_password,
            role=models.UserRole.admin
        )

        db.add(new_admin)
        db.commit()
        print("Admin user created.")

    except Exception as e:
        print("Error creating admin:", e)

    finally:
        db.close()



@app.get('/')
def root():
    return {"message " : "Hello world"}