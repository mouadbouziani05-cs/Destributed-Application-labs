@app.post("/api/v1/users")
def create_user_v1(user: UserV1):
    return {"version": "v1", "user": user}

@app.post("/api/v2/users")
def create_user_v2(user: UserV2):
    return {"version": "v2", "user": user}
{
  "name": "Douaa"
}
