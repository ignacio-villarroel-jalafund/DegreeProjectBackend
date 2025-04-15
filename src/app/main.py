from fastapi import FastAPI
from app.api.v1.api import api_router as api_router_v1


app = FastAPI(
    title="Recipe & User Service API",
    description="API to manage users and recipes. Enter your JWT token (Bearer Token) to access protected endpoints.",
    version="1.0.0",
    
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

app.include_router(api_router_v1, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Users and Recipes Service!"}

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(   
     CORSMiddleware,
     allow_origins=["*"],
     allow_credentials=True,
     allow_methods=["*"],
     allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)