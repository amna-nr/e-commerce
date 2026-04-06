from pydantic import BaseModel
from typing import Optional


class ProductIn(BaseModel):
    title: str
    price: int
    stock: int

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[int] = None
    stock: Optional[int] = None

class ProductOut(ProductIn):
    id: int

    class Config():
        from_attributes=True