from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
from security import SECRET_KEY, ALGORITHM

security = HTTPBearer()

def verify_token(credentials=Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")
