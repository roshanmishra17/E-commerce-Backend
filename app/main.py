from fastapi import FastAPI
from . database import SessionLocal, engine,get_db
from . import models
from . routers import users,auth

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


app.include_router(users.router)
app.include_router(auth.router)



@app.get('/')
def root():
    return {"message " : "Hello world"}