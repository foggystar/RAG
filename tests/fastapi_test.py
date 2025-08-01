from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/items/{id}")     # POST 请求到 /items
async def get_items(id: int):
    return {"item": id}