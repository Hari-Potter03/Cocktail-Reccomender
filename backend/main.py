from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router

app = FastAPI(title="Cocktail Recommender API")

# allow your React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "ok": True,
        "message": "Cocktail Recommender API",
        "endpoints": ["/drinks", "/search", "/similar/{id}", "/recs", "/ratings", "/docs"]
    }

app.include_router(router)
