from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from starlette import status 
from sqlalchemy import delete

from app.core.database import db_dependency
from app.models.models import User, Product
from app.auth.service import get_current_user
from app.products.schemas import ProductIn, ProductOut, ProductUpdate



router = APIRouter(
    prefix="/products",
    tags=["products"]
)


# show all products
@router.get("/", response_model=list[ProductOut])
async def products_list(db: db_dependency, user: User = Depends(get_current_user)):

    result = await db.execute(select(Product))
    products = result.scalars().all()
    return products
    

# create new product
@router.post("/", response_model=ProductOut)
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
@router.put("/{id}")
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
    
    for key, value in product_update.model_dump(exclude_unset=True).items():
        setattr(product, key, value)

    await db.commit()
    await db.refresh(product)

    return product


# delete product 
@router.delete("/{id}")
async def products_delete(id: int, db: db_dependency, user: User = Depends(get_current_user)):

    # delete product directly
    result = await db.execute(delete(Product).where(Product.id == id))

    # check how many rows were affected 
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Product not found."
            )
    
    # save changes 
    await db.commit()

    return {"message" : "Product has been deleted"}