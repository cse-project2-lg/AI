# app/evaluation/retrieval_test.py

from app.rag.retrieval.retriever import JsonRetriever


TEST_QUERIES = [
    "PIR 센서 데이터는 어떤 형식으로 수집되어야 하는가?",
    "ToF 센서는 낙상 감지에서 어떤 역할을 하는가?",
    "CSI 데이터는 사용자 행동 인식에서 어떻게 활용되는가?",
    "낙상 후보가 감지되면 사용자에게 어떤 확인 절차를 수행하는가?",
    "보호자 알림은 어떤 상황에서 전송되는가?",
    "센서 데이터는 어떤 통신 방식으로 전달되는가?",
    "관리자 화면에는 어떤 정보가 표시되어야 하는가?",
    "클라우드 AI 또는 LLM이 실패하면 시스템은 어떻게 대응해야 하는가?",
]


def run_retrieval_test() -> None:
    retriever = JsonRetriever(
        embedding_file_path="data/chunks/chunk_embeddings.json"
    )

    for query_index, query in enumerate(TEST_QUERIES, start=1):
        print("=" * 80)
        print(f"[Query {query_index}] {query}")

        results = retriever.retrieve(query=query, top_k=3)

        for result_index, result in enumerate(results, start=1):
            metadata = result["metadata"]

            print(f"\n  [{result_index}] rerank_score: {result['rerank_score']:.4f}")
            print(f"      final_score: {result['final_score']:.4f}")
            print(f"      embedding_score: {result['embedding_score']:.4f}")
            print(f"      keyword_score: {result['keyword_score']:.4f}")
            print(f"      metadata_score: {result['metadata_score']:.4f}")
            print(f"      section_boost: {result['section_boost']:.4f}")
            print(f"      text_boost: {result['text_boost']:.4f}")
            print(f"      category_penalty: {result['category_penalty']:.4f}")
            print(f"      context_penalty: {result['context_penalty']:.4f}")
            print(f"      section_title: {metadata.get('section_title')}")
            print(f"      category: {metadata.get('category')}")
            print(f"      priority: {metadata.get('priority')}")
            print(f"      chunk_index: {metadata.get('chunk_index')}")
            print(f"      text_preview: {result['text'][:180].replace(chr(10), ' ')}")
            print(f"      intent_weights: {result.get('intent_weights', {})}")
            print(f"      intent_priority_boost: {result['intent_priority_boost']:.4f}")
            print(f"      intent_priority_penalty: {result['intent_priority_penalty']:.4f}")
if __name__ == "__main__":
    run_retrieval_test()