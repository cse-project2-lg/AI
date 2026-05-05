from typing import Dict, Any, List

# 센서 이벤트 데이터를 RAG 검색에 적합한 자연어 query로 변환
def generate_query_from_event(sensor_event: Dict[str, Any]) -> str:

    query_parts: List[str] = []

    pir_detected = sensor_event.get("pir_detected")
    tof_distance_drop_cm = sensor_event.get("tof_distance_drop_cm")
    csi_variance_level = sensor_event.get("csi_variance_level")
    user_response = sensor_event.get("user_response")
    llm_status = sensor_event.get("llm_status")
    event_type = sensor_event.get("event_type", "fall_candidate")

    if pir_detected is True:
        query_parts.append("PIR 센서에서 사용자의 움직임이 감지됨")
    elif pir_detected is False:
        query_parts.append("PIR 센서에서 사용자의 움직임이 감지되지 않음")

    if tof_distance_drop_cm is not None:
        query_parts.append(f"ToF 거리 값이 {tof_distance_drop_cm}cm 급격히 감소함")

    if csi_variance_level:
        if csi_variance_level == "high":
            query_parts.append("CSI 신호 변화량이 크게 증가함")
        elif csi_variance_level == "medium":
            query_parts.append("CSI 신호 변화량이 중간 수준으로 관찰됨")
        elif csi_variance_level == "low":
            query_parts.append("CSI 신호 변화량이 낮게 관찰됨")
        else:
            query_parts.append(f"CSI 신호 변화 수준이 {csi_variance_level}로 관찰됨")

    if user_response == "no_response":
        query_parts.append("사용자 확인 요청에 응답이 없음")
    elif user_response == "responded":
        query_parts.append("사용자가 확인 요청에 응답함")
    elif user_response == "movement_detected":
        query_parts.append("확인 요청 이후 사용자의 움직임이 다시 감지됨")

    if llm_status == "failed":
        query_parts.append("클라우드 AI 또는 LLM 판단이 실패함")
    elif llm_status == "available":
        query_parts.append("클라우드 AI 또는 LLM 판단이 가능한 상태임")

    if event_type == "fall_candidate":
        purpose = "낙상 후보 판단 기준과 사용자 확인 및 보호자 알림 대응 절차"
    elif event_type == "notification":
        purpose = "보호자 알림 전송 조건과 알림 처리 방식"
    elif event_type == "admin_display":
        purpose = "관리자 화면에 표시해야 하는 상태 정보와 로그 정보"
    elif event_type == "llm_failure":
        purpose = "클라우드 AI 실패 시 로컬 대응 및 대체 처리 정책"
    else:
        purpose = "관련 시스템 요구사항과 대응 정책"

    if not query_parts:
        return f"{purpose}를 검색한다."

    event_description = ", ".join(query_parts)

    return f"{event_description} 상황에서 {purpose}를 검색한다."