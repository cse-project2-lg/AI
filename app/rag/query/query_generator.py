from typing import Any, Dict, List


# 최종 /event/candidate JSON을 RAG 검색에 적합한 자연어 query로 변환한다.
def generate_query_from_event(sensor_event: Dict[str, Any]) -> str:
    sensor = sensor_event.get("sensorSummary", {})

    query_parts: List[str] = []

    pir_motion = sensor.get("pirMotion")
    pir_last_motion_ms = sensor.get("pirLastMotionMs")
    tof_change_mm = sensor.get("tofChangeMm")
    tof_stable_ms = sensor.get("tofStableMs")
    csi_score = sensor.get("csiChangeScore")
    csi_packet_count = sensor.get("csiPacketCount")
    local_score = sensor_event.get("localScore")

    if pir_motion is True:
        query_parts.append("PIR 센서에서 움직임이 감지됨")
    elif pir_motion is False:
        query_parts.append("PIR 센서에서 움직임이 감지되지 않음")

    if pir_last_motion_ms is not None:
        query_parts.append(f"마지막 PIR 움직임 이후 {pir_last_motion_ms}ms 경과")

    if tof_change_mm is not None:
        query_parts.append(f"ToF 거리 변화량이 {tof_change_mm}mm로 관찰됨")

    if tof_stable_ms is not None:
        query_parts.append(f"ToF 변화 상태가 {tof_stable_ms}ms 동안 유지됨")

    if csi_score is not None:
        if csi_score >= 0.7:
            query_parts.append("CSI 변화 점수가 높음")
        elif csi_score >= 0.4:
            query_parts.append("CSI 변화 점수가 중간 수준")
        else:
            query_parts.append("CSI 변화 점수가 낮음")

    if csi_packet_count is not None:
        query_parts.append(f"최근 CSI 패킷 수는 {csi_packet_count}개")

    if local_score is not None:
        query_parts.append(f"엣지 로컬 낙상 후보 점수는 {local_score}")

    purpose = "낙상 후보 판단 기준, 사용자 확인 절차, 보호자 알림 대응 정책"

    if not query_parts:
        return f"{purpose}를 검색한다."

    event_description = ", ".join(query_parts)
    return f"{event_description} 상황에서 {purpose}를 검색한다."
