from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import inventory, forecast, decisions, agent

app = FastAPI(title="Inventory Agent API", version="1.0.0")

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True)

app.include_router(inventory.router, prefix="/api")
app.include_router(forecast.router, prefix="/api")
app.include_router(decisions.router, prefix="/api")
app.include_router(agent.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}