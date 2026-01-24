from fastapi import FastAPI
from . database import SessionLocal, engine,get_db
from . import models
from . routers import users,auth,categories,products,inventory,cart,orders
from . config import settings
from sqlalchemy.orm import Session
from . utils import hash_pass
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()




ADMIN_EMAIL = settings.ADMIN_EMAIL
ADMIN_PASSWORD = settings.ADMIN_PASSWORD

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(users.router)
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(cart.router)
app.include_router(orders.router)

@app.on_event("startup")
def create_initial_admin():
    models.Base.metadata.create_all(bind=engine)
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