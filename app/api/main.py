from fastapi import FastAPI

from app.api.schemas import FallAnalyzeRequest, FallAnalyzeResponse, FallOutcomeRequest
from app.llm.rag_analyzer import analyze_sensor_event_with_rag


app = FastAPI(title="Fall Detection AI/RAG API", version="1.0.0")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/v1/fall-events/analyze", response_model=FallAnalyzeResponse)
def analyze_fall_event(request: FallAnalyzeRequest):
    result = analyze_sensor_event_with_rag(request.dict())
    return result


@app.post("/api/v1/fall-events/outcome")
def save_fall_outcome(request: FallOutcomeRequest):
    # TODO: Save to DB or log storage.
    print("OUTCOME:", request.dict())
    return {"saved": True}
