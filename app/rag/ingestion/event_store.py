from typing import Dict, Any, Tuple, List
from app.rag.embeddings.embedder import Embedder

_embedder = None


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder


def build_embedding_payload(
    sensor_event: Dict[str, Any],
    llm_result: Dict[str, Any],
) -> Tuple[str, List[float]]:
    content_text = (
        f"CSI변화율={sensor_event.get('localScore')} "
        f"PIR={sensor_event.get('sensorSummary', {}).get('pirMotion')} "
        f"ToF변화={sensor_event.get('sensorSummary', {}).get('tofChangeMm')}mm "
        f"판단={'낙상' if llm_result.get('isFall') else '정상'} "
        f"위험도={llm_result.get('riskLevel')} "
        f"근거={llm_result.get('analysisReason', '')}"
    )
    embedding = get_embedder().embed_text(content_text)
    return content_text, embedding