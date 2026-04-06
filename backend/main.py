from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette import status 
from contextlib import asynccontextmanager
from app.core.redis import redis_client
from sqlalchemy import select

from app.auth.auth import get_current_user, router as auth_router
from app.core.database import db_dependency
from app.models.models import User, Product
from app.schemas.schemas import ProductIn, ProductOut, ProductUpdate


# start redis on startup and close on shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.ping()
    yield 
    await redis_client.aclose()

app = FastAPI(lifespan=lifespan)

# include auth routes
app.include_router(auth_router)

# enable frontend to access backend on the browser
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


# show all products
@app.get("/products", response_model=list[ProductOut])
async def products_list(db: db_dependency, user: User = Depends(get_current_user)):

    result = await db.execute(Product)
    products = result.scalars().all()
    return products
    

# create new product
@app.post("/products", response_model=list[ProductOut])
async def products_create(product: ProductIn, db: db_dependency, user: User = Depends(get_current_user)):

    new_product = Product(
        title = product.title,
        price = product.price, 
        stock = product.stock
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    return new_product


# update existing product
@app.put("/products/{id}")
async def products_update(id: int, product_update: ProductUpdate, db: db_dependency, user: User = Depends(get_current_user)):

    # get product from db
    result = await db.execute(select(Product).where(Product.id == id))
    product = result.scalar_one_or_none()

    # check if product exists
    if not product: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
            )
    
    for key, value in product_update.dict(exclude_unset=True).items():
        setattr(product, key, value)

    await db.commit()
    await db.refresh(product)

    return product


# delete product 
@app.delete("/products/{id}")
async def products_delete(id: int, db: db_dependency, user: User = Depends(get_current_user)):

    # get product from db 
    result = await db.execute(select(Product).where(Product.id == id))
    product = result.scalar_one_or_none()

    # check if product exists
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Product not found."
            )
    
    # delete the product 
    await db.delete(product)
    await db.commit()

    return {"message" : "Product has been deleted"}