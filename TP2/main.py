from fastapi import FastAPI, HTTPException, Depends
from security import verify_password, create_token
from database import users_db, documents_db
from auth import verify_token
import uuid

app = FastAPI()

# ---------------- AUTH ---------------- #

@app.post("/api/v1/auth/login")
def login(data: dict):
    if "username" not in data or "password" not in data:
        raise HTTPException(status_code=400, detail="Champs manquants")

    user = users_db.get(data["username"])

    # éviter de dire si user existe
    if not user or not verify_password(data["password"], user["password"]):
        raise HTTPException(status_code=401, detail="Credentials invalides")

    token, exp = create_token({"user_id": user["id"], "roles": user["roles"]})

    return {"token": token, "expires_at": exp}


@app.get("/api/v1/auth/verify")
def verify(user=Depends(verify_token)):
    return {"valid": True, "user_id": user["user_id"], "roles": user["roles"]}


# ---------------- DOCUMENTS ---------------- #

@app.post("/api/v1/documents")
def create_doc(data: dict, user=Depends(verify_token)):
    if "title" not in data or "content" not in data:
        raise HTTPException(status_code=400, detail="Validation error")

    doc_id = str(uuid.uuid4())

    documents_db[doc_id] = {
        "id": doc_id,
        "title": data["title"],
        "content": data["content"],
        "owner": user["user_id"]
    }

    return {"id": doc_id, "title": data["title"]}


@app.get("/api/v1/documents")
def list_docs(user=Depends(verify_token)):
    return {"data": list(documents_db.values()), "total": len(documents_db)}


@app.get("/api/v1/documents/{doc_id}")
def get_doc(doc_id: str, user=Depends(verify_token)):
    doc = documents_db.get(doc_id)

    if not doc:
        raise HTTPException(status_code=404)

    if doc["owner"] != user["user_id"]:
        raise HTTPException(status_code=403)

    return doc


@app.put("/api/v1/documents/{doc_id}")
def update_doc(doc_id: str, data: dict, user=Depends(verify_token)):
    doc = documents_db.get(doc_id)

    if not doc:
        raise HTTPException(status_code=404)

    if doc["owner"] != user["user_id"]:
        raise HTTPException(status_code=403)

    doc.update(data)
    return doc


@app.delete("/api/v1/documents/{doc_id}")
def delete_doc(doc_id: str, user=Depends(verify_token)):
    doc = documents_db.get(doc_id)

    if not doc:
        raise HTTPException(status_code=404)

    if doc["owner"] != user["user_id"]:
        raise HTTPException(status_code=403)

    del documents_db[doc_id]
    return {}
    

# ---------------- SEARCH ---------------- #

@app.get("/api/v1/search")
def search(q: str = "", user=Depends(verify_token)):
    if not q:
        raise HTTPException(status_code=400, detail="Query vide")

    results = [doc for doc in documents_db.values() if q in doc["title"]]

    return {"results": results, "total": len(results)}
