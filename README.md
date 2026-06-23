# AI (LLM + RAG 기반 낙상 판정 모듈)

## 개요

본 리포지토리는 Wi-Fi CSI 기반 비접촉 낙상 감지 시스템의 **AI 판정 파이프라인**을 담당한다.

Edge(Raspberry Pi 4)에서 Rule 기반으로 1차 필터링된 낙상 후보 이벤트를 FastAPI로 수신하여, **Google Gemini API**와 **RAG(Retrieval-Augmented Generation)** 검색을 결합해 낙상 여부 및 권장 대응을 최종 판정한다.

판정 결과는 `isFall`, `confidence`, `riskLevel`, `recommendedAction`, `verificationPlan` 등을 포함한 구조화된 JSON으로 반환되며, 이는 사용자 확인(TTS/STT) 및 보호자 알림 흐름의 입력으로 사용된다.

---

## 기술 스택

- **Language**: Python 3.10+
- **API Server**: FastAPI + Uvicorn
- **Validation**: Pydantic v2
- **LLM**: Google Gemini (`google-genai`)
- **RAG / Embedding**: `sentence-transformers`
- **수치 연산**: NumPy
- **문서 처리**: `python-docx` (SRS 등 문서 파싱용)
- **환경변수**: `python-dotenv`

---

## 리포지토리 구조

```
AI/
├── app/
│   ├── api/
│   │   ├── main.py              # FastAPI 엔트리포인트, 라우트 정의
│   │   └── schemas.py           # 요청/응답 Pydantic 스키마
│   ├── llm/
│   │   ├── gemini_client.py     # Gemini API 클라이언트
│   │   └── rag_analyzer.py      # RAG 결과 + LLM 호출 → 최종 판정 결합
│   ├── rag/
│   │   ├── ingestion/           # 지식베이스 로딩·청크 분할·정제 (loader, chunker, cleaner, ingest_pipeline, event_store, metadata)
│   │   ├── embeddings/          # 임베딩 생성 (embedder, embedding_service)
│   │   ├── retrieval/           # 검색/리랭킹 (retriever, pg_retriever, reranker, scoring, similarity)
│   │   ├── query/               # 검색 질의 생성 (query_generator)
│   │   ├── prompt/              # 증강 프롬프트 빌드 (prompt_builder)
│   │   ├── context/             # 이벤트 컨텍스트 구성 (context_builder)
│   │   ├── schemas/             # RAG 문서/청크 스키마 (document, chunk)
│   │   ├── utils/                # 공용 유틸 (file_utils, text_utils)
│   │   ├── evaluation/           # 검색 품질 평가 (retrieval_test)
│   │   └── rag_test.py
│   └── evaluate.py              # Rule-based / LLM-only / LLM+RAG 비교 평가 스크립트
├── data/
│   ├── raw/
│   │   ├── knowledge_base/      # RAG 지식베이스 원본 (낙상 정의, 오탐 사례, 센서 패턴 가이드)
│   │   └── srs/                 # 요구사항분석서(SRS) 원본 문서
│   └── chunks/
│       ├── chunks.json          # 분할된 지식베이스 청크
│       └── chunk_embeddings.json # 청크별 임베딩 벡터
├── eval_results*.json           # 평가 결과 로그
├── requirements.txt
└── README.md
```

---

## API 엔드포인트

FastAPI 서버(`app/api/main.py`)는 다음 엔드포인트를 제공한다.

| Method | Path | 설명 |
|---|---|---|
| GET | `/health` | 헬스 체크 |
| POST | `/api/v1/fall-events/analyze` | 낙상 후보 이벤트(`event.candidate`)를 받아 LLM+RAG 판정 수행, `analysis.result` 반환 |
| POST | `/api/v1/notifications/guardian` | 보호자 알림 요청 처리 (현재 MVP stub) |
| POST | `/api/v1/fall-events/outcome` | 최종 대응 결과(`response.outcome`) 저장 (현재 stub, DB 연동 예정) |

### 주요 요청/응답 스키마 (`app/api/schemas.py`)

- `FallAnalyzeRequest` — `sensorSummary`(PIR/ToF/CSI), `localScore`, `localRiskLevel`, `candidateReason` 등 Edge의 1차 판정 정보를 포함
- `FallAnalyzeResponse` — `isFall`, `confidence`, `riskLevel`, `recommendedAction`(`NO_ACTION`/`OBSERVE`/`VERIFY_USER`/`NOTIFY_GUARDIAN`), `verificationPlan`, `analysisStatus`(`SUCCESS`/`FALLBACK_RULE`/`FAILED`)
- `NotificationRequest` / `NotificationResult` — 보호자 알림 트리거 및 결과
- `FallOutcomeRequest` — 사용자 응답(`userResponse`), 최종 대응 결과(`responseOutcome`)를 포함한 종결 보고

---

## 개발 환경 세팅

### 1. Repository Clone

```bash
git clone https://github.com/cse-project2-lg/AI.git
cd AI
```

### 2. Python 가상환경 구성

```bash
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install --upgrade pip
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

설치되는 주요 패키지: `fastapi`, `uvicorn`, `pydantic>=2.0.0,<3.0.0`, `python-dotenv`, `google-genai`, `sentence-transformers`, `numpy`, `python-docx`

### 4. 환경 변수 설정 (`.env`)

```env
GOOGLE_API_KEY=<Gemini API Key>
# 또는 Vertex AI / ADC 사용 시 GCP 프로젝트 및 인증 정보
```

### 5. 서버 실행

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

헬스 체크:

```bash
curl http://localhost:8000/health
```

---

## 평가 (`app/evaluate.py`)

세 가지 조건(Rule-based / LLM-only / LLM+RAG)에 대해 Precision, Recall, F1, Latency를 비교 평가한다. 결과는 `eval_results.json`, `eval_results_*.json`에 저장된다.

```bash
python -m app.evaluate
```

---

## 관련 리포지토리

- [전체 프로젝트 개요 (Organization)](https://github.com/cse-project2-lg)
