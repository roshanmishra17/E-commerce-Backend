from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"],deprecated = "auto")

def hash_pass(password : str):
    return pwd_context.hash(password)

def verify(password,hash_pass):
    return pwd_context.verify(password,hash_pass)

