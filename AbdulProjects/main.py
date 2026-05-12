                        #craeted a fast api

from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()

class Product(BaseModel):
    name:str
    price: int

@app.post("/products")
def craete_pro(product: Product):

    product_dict = {
        "name": product.name,
        "price": product.price
    
    }
    product.append(product_dict)

    return{
        "message": "Product Created",
        "product": product_dict
    }

app.get("/products")
def get_product():

    return{
        "products": products
    }