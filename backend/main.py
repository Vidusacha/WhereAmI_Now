from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import entities, axes, sources, questions, documents, entity_types

app = FastAPI(title="WhereAmI V2 API", version="2.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(entities.router, prefix="/api/entities", tags=["Entities"])
app.include_router(axes.router, prefix="/api/axes", tags=["Axes"])
app.include_router(questions.router, prefix="/api/questions", tags=["Questions"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(entity_types.router, prefix="/api/entity_types", tags=["Entity Types"])
app.include_router(sources.router, prefix="/api/sources", tags=["Static Sources"])

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}
