from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import parties, axes, sources

app = FastAPI(title="WhereAmI V2 API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parties.router, prefix="/api/parties", tags=["Parties"])
app.include_router(axes.router, prefix="/api/axes", tags=["Axes"])
app.include_router(sources.router, prefix="/api/sources", tags=["Static Sources"])

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}
