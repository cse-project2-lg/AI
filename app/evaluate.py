"""
논문 평가 스크립트: Rule-based vs LLM 단독 vs LLM+RAG 비교
==========================================================
사용법:
    python evaluate.py --dataset test_data.json
    python evaluate.py --dataset test_data.json --conditions A C
    python evaluate.py --dataset test_data.json --no-api

데이터셋 JSON 형식:
[
  {
    "label": true,
    "scenario": "낙상_전형적",
    "event": { ... FallAnalyzeRequest 형식 ... }
  },
  ...
]

결과: Accuracy, Precision, Recall, F1-score 출력 (조건 A/B/C)
"""

import json
import sys
import time
import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# --------------------------------------------------------------------------
# 1. 데이터셋 로드
# --------------------------------------------------------------------------

def load_dataset(path: str) -> List[Dict[str, Any]]:
    """
    외부 JSON 파일에서 데이터셋을 로드한다.

    필수 필드:
      - label (bool): True = 낙상, False = 비낙상
      - event (dict): FallAnalyzeRequest 형식의 센서 이벤트
    선택 필드:
      - scenario (str): 시나리오 설명 (없으면 eventId로 대체)
    """
    p = Path(path)
    if not p.exists():
        print(f"[오류] 데이터셋 파일을 찾을 수 없습니다: {p.resolve()}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[오류] JSON 파싱 실패: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list) or len(data) == 0:
        print("[오류] 데이터셋은 비어있지 않은 JSON 배열이어야 합니다.", file=sys.stderr)
        sys.exit(1)

    validated = []
    for i, item in enumerate(data):
        if "label" not in item or "event" not in item:
            print(f"[경고] 샘플 #{i} 에 'label' 또는 'event' 필드가 없어 건너뜁니다.", file=sys.stderr)
            continue
        if "scenario" not in item:
            item["scenario"] = item["event"].get("eventId", f"sample_{i}")
        item["label"] = bool(item["label"])
        validated.append(item)

    print(f"[데이터셋] {p.name} 로드 완료 — {len(validated)}개 샘플 "
          f"(낙상: {sum(1 for d in validated if d['label'])}, "
          f"비낙상: {sum(1 for d in validated if not d['label'])})")
    return validated


# --------------------------------------------------------------------------
# 2. 조건 A: Rule-based 판단
# --------------------------------------------------------------------------
# 실제 실험 시 반드시 --dataset 인자로 데이터셋 파일을 지정하세요.
# --------------------------------------------------------------------------

def rule_based_predict(event: Dict[str, Any]) -> bool:
    """
    Rule-based 낙상 판단 (조건 A)
    
    기준:
    - localScore >= 0.7 → 낙상 판단
    - tofChangeMm <= -1000 AND pirLastMotionMs >= 2000 → 낙상 판단
    - csiChangeScore >= 0.75 AND tofChangeMm <= -800 → 낙상 판단
    """
    sensor = event.get("sensorSummary", {})
    local_score = event.get("localScore", 0.0)
    tof_change = sensor.get("tofChangeMm", 0)
    pir_last_ms = sensor.get("pirLastMotionMs", 0)
    csi = sensor.get("csi", {})
    csi_score = csi.get("changeScore") or 0.0

    if local_score >= 0.70:
        return True
    if tof_change <= -1000 and pir_last_ms >= 2000:
        return True
    if csi_score >= 0.75 and tof_change <= -800:
        return True
    return False


# --------------------------------------------------------------------------
# 3. 조건 B: LLM 단독 (Gemini, RAG 없음)
# --------------------------------------------------------------------------

def llm_only_predict(event: Dict[str, Any]) -> bool:
    """LLM 단독 판단 (조건 B) — RAG 없이 Gemini에게 직접 질의"""
    try:
        from app.llm.gemini_client import analyze_with_gemini
        from app.llm.rag_analyzer import parse_llm_json, normalize_response

        prompt = f"""
너는 낙상 감지 시스템이다.
아래 센서 이벤트를 보고 낙상 여부를 판단하라.
반드시 JSON만 출력하라.

[센서 이벤트]
{json.dumps(event, ensure_ascii=False)}

[출력 형식]
{{
  "type": "analysis.result",
  "eventId": "{event.get('eventId')}",
  "timestamp": "",
  "isFall": true,
  "confidence": 0.0,
  "riskLevel": "LOW | MEDIUM | HIGH",
  "recommendedAction": "NO_ACTION | OBSERVE | VERIFY_USER | NOTIFY_GUARDIAN",
  "situationSummary": "요약",
  "analysisReason": "근거",
  "verificationPlan": {{"required": false, "method": "NONE", "promptAsset": null, "expectedOkText": [], "timeoutSec": 0}},
  "analysisStatus": "SUCCESS"
}}
""".strip()

        raw = analyze_with_gemini(prompt)
        parsed = parse_llm_json(raw)
        normalized = normalize_response(parsed, event)
        return bool(normalized.get("isFall", False))

    except Exception as e:
        print(f"  [LLM-Only 오류] {event.get('eventId')}: {e}", file=sys.stderr)
        event["fallback"] = True
        return event.get("localScore", 0.0) >= 0.70


# --------------------------------------------------------------------------
# 4. 조건 C: LLM + RAG (기존 시스템)
# --------------------------------------------------------------------------

def llm_rag_predict(event: Dict[str, Any]) -> bool:
    """LLM + RAG 판단 (조건 C) — 기존 analyze_sensor_event_with_rag 사용"""
    try:
        from app.llm.rag_analyzer import analyze_sensor_event_with_rag
        result = analyze_sensor_event_with_rag(event)
        return bool(result.get("isFall", False))
    except Exception as e:
        print(f"  [LLM+RAG 오류] {event.get('eventId')}: {e}", file=sys.stderr)
        return event.get("localScore", 0.0) >= 0.70


# --------------------------------------------------------------------------
# 5. 평가 지표 계산
# --------------------------------------------------------------------------

@dataclass
class EvalResult:
    condition: str
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0
    latencies: List[float] = field(default_factory=list)
    per_sample: List[Dict] = field(default_factory=list)

    @property
    def total(self): return self.tp + self.fp + self.tn + self.fn

    @property
    def accuracy(self):
        return (self.tp + self.tn) / self.total if self.total else 0.0

    @property
    def precision(self):
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else 0.0

    @property
    def recall(self):
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else 0.0

    @property
    def f1(self):
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    @property
    def avg_latency_ms(self):
        return sum(self.latencies) / len(self.latencies) * 1000 if self.latencies else 0.0

    def to_dict(self):
        return {
            "condition": self.condition,
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "tp": self.tp, "fp": self.fp, "tn": self.tn, "fn": self.fn,
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "per_sample": self.per_sample,
        }


def evaluate(condition_name: str, predict_fn, dataset: List[Dict]) -> EvalResult:
    result = EvalResult(condition=condition_name)
    print(f"\n[{condition_name}] 평가 시작 ({len(dataset)}개 샘플)")

    for item in dataset:
        event = item["event"]
        label = item["label"]
        scenario = item["scenario"]

        t0 = time.monotonic()
        predicted = predict_fn(event)
        elapsed = time.monotonic() - t0

        result.latencies.append(elapsed)

        if label and predicted:
            result.tp += 1; outcome = "TP"
        elif not label and predicted:
            result.fp += 1; outcome = "FP ⚠"
        elif label and not predicted:
            result.fn += 1; outcome = "FN ⚠"
        else:
            result.tn += 1; outcome = "TN"

        result.per_sample.append({
            "eventId": event.get("eventId"),
            "scenario": scenario,
            "label": label,
            "predicted": predicted,
            "outcome": outcome,
            "latency_ms": round(elapsed * 1000, 1),
            "fallback": event.get("fallback", False),
        })
        print(f"  {outcome:5s} | {scenario:30s} | {elapsed*1000:6.0f}ms")

    print(f"  → Acc={result.accuracy:.3f}  Pre={result.precision:.3f}  "
          f"Rec={result.recall:.3f}  F1={result.f1:.3f}  "
          f"AvgLat={result.avg_latency_ms:.0f}ms")
    
    fallback_count = sum(1 for s in result.per_sample if s.get("fallback"))
    if fallback_count:
        print(f"  ⚠ 폴백 발생: {fallback_count}/{len(result.per_sample)} (결과 신뢰도 낮음)")

    return result


# --------------------------------------------------------------------------
# 6. 메인 실행
# --------------------------------------------------------------------------

def print_summary(results: List[EvalResult]):
    print("\n" + "="*70)
    print("  논문 평가 결과 요약")
    print("="*70)
    header = f"{'조건':<20} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10} {'AvgLat(ms)':>12}"
    print(header)
    print("-"*70)
    for r in results:
        print(f"{r.condition:<20} {r.accuracy:>10.4f} {r.precision:>10.4f} "
              f"{r.recall:>10.4f} {r.f1:>10.4f} {r.avg_latency_ms:>12.1f}")
    print("="*70)

    print("\n  오탐/미탐 상세")
    print(f"{'조건':<20} {'TP':>5} {'FP':>5} {'TN':>5} {'FN':>5}")
    print("-"*40)
    for r in results:
        print(f"{r.condition:<20} {r.tp:>5} {r.fp:>5} {r.tn:>5} {r.fn:>5}")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(description="낙상 감지 시스템 평가 스크립트")
    parser.add_argument(
        "--dataset", default=None,
        help="테스트 데이터셋 JSON 파일 경로 (없으면 내장 예시 데이터 사용)"
    )
    parser.add_argument("--output", default="eval_results.json", help="결과 저장 경로")
    parser.add_argument(
        "--conditions", nargs="+",
        choices=["A", "B", "C"], default=["A", "B", "C"],
        help="실행할 조건 (A=Rule-based, B=LLM-only, C=LLM+RAG)"
    )
    parser.add_argument(
        "--no-api", action="store_true",
        help="API 호출 없이 Rule-based(A)만 실행 (API 키 없을 때 사용)"
    )
    args = parser.parse_args()

    # 데이터셋 로드
    if args.dataset:
        dataset = load_dataset(args.dataset)
    else:
        print("[경고] --dataset 미지정. 내장 예시 데이터로 실행합니다.")
        print("  실제 실험 시에는 --dataset test_data.json 으로 지정하세요.\n")
        dataset = _EXAMPLE_DATASET

    # --no-api 플래그가 있으면 A만
    if args.no_api:
        args.conditions = ["A"]

    results: List[EvalResult] = []
    condition_map = {
        "A": ("A. Rule-based",     rule_based_predict),
        "B": ("B. LLM 단독",       llm_only_predict),
        "C": ("C. LLM+RAG (제안)", llm_rag_predict),
    }

    for cond in args.conditions:
        name, fn = condition_map[cond]

        if cond in ("B", "C") and dataset:
            print(f"[{name}] 워밍업 중...")
            try:
                fn(dataset[0]["event"])
            except Exception:
                print(f"[{name}] 워밍업 중 오류 발생")
                pass

        r = evaluate(name, fn, dataset)
        results.append(r)

    print_summary(results)

    # JSON 저장
    output_data = {
        "evaluated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "dataset_file": args.dataset or "(내장 예시 데이터)",
        "total_samples": len(dataset),
        "sample_breakdown": {
            "fall": sum(1 for d in dataset if d["label"]),
            "non_fall": sum(1 for d in dataset if not d["label"]),
        },
        "results": [r.to_dict() for r in results],
    }

    output_path = Path(args.output)
    output_path.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n결과 저장: {output_path.resolve()}")


if __name__ == "__main__":
    main()