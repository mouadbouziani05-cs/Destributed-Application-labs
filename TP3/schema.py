from typing import Optional

class UserV1(BaseModel):
    name: str

class UserV2(BaseModel):
    name: str
    email: Optional[str] = None
{
  "name": "Douaa"
}
