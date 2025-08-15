from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router

app = FastAPI(title="Cocktail Recommender API")

# allow your React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:3000", "http://127.0.0.1:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,  # only True if you use cookies/sessions
)


@app.get("/")
def root():
    return {
        "ok": True,
        "message": "Cocktail Recommender API",
        "endpoints": ["/drinks", "/search", "/similar/{id}", "/recs", "/ratings", "/docs"]
    }

app.include_router(router)
