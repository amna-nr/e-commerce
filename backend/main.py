from fastapi import FastAPI, Depends, HTTPException
from auth import get_current_user, router as auth_router
from database import db_dependency, create_tables
from models import User, Product
from schemas import ProductIn, ProductOut, ProductUpdate
from fastapi.middleware.cors import CORSMiddleware
from starlette import status 
from redis import Redis 
import httpx
import json

app = FastAPI()

app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "welcome"}

@app.get("/products", response_model=list[ProductOut])
def products_list(db: db_dependency, user: User = Depends(get_current_user)):
    products = db.query(Product).all()
    return products

@app.post("/products", response_model=list[ProductOut])
def products_create(product: ProductIn, db: db_dependency, user: User = Depends(get_current_user)):
    new_product = Product(
        title = product.title,
        price = product.price, 
        stock = product.stock
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@app.put("/products/{id}")
def products_update(id: int, product_update: ProductUpdate, db: db_dependency, user: User = Depends(get_current_user)):

    product = db.query(Product).filter(Product.id == id).first()

    if not product: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    for key, value in product_update.dict(exclude_unset=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    return product


@app.delete("/products/{id}")
def products_delete(id: int, db: db_dependency, user: User = Depends(get_current_user)):

    product = db.query(Product).filter(Product.id == id).first()

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    
    db.delete(product)
    db.commit()

    return {"message" : "Product has been deleted"}