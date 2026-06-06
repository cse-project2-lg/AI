from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


CsiStatus = Literal["AVAILABLE", "UNAVAILABLE", "STUB"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
RecommendedAction = Literal["NO_ACTION", "OBSERVE", "VERIFY_USER", "NOTIFY_GUARDIAN"]
UserResponse = Literal["NOT_ASKED", "OK", "NOT_OK", "HELP", "NO_RESPONSE", "UNCLEAR"]
ResponseOutcome = Literal[
    "NORMAL_CLOSED",
    "OBSERVING",
    "VERIFIED_OK_CLOSED",
    "ESCALATED_TO_GUARDIAN",
    "NOTIFICATION_FAILED",
]
NotificationStatus = Literal["NOT_REQUIRED", "PENDING", "SENT", "FAILED"]
AnalysisStatus = Literal["SUCCESS", "FALLBACK_RULE", "FAILED"]
VerificationMethod = Literal["NONE", "LOCAL_MP3_STT"]


class CsiSummary(BaseModel):
    status: CsiStatus
    changeScore: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    packetCount: Optional[int] = Field(default=None, ge=0)
    reason: Optional[str] = None


class EventWindow(BaseModel):
    startMonotonicNs: int = Field(ge=0)
    endMonotonicNs: int = Field(ge=0)
    durationMs: int = Field(ge=0)

    @model_validator(mode="after")
    def check_time_consistency(self):
        if self.endMonotonicNs < self.startMonotonicNs:
            raise ValueError("endMonotonicNs는 startMonotonicNs보다 크거나 같아야 합니다.")
        expected_ms = (self.endMonotonicNs - self.startMonotonicNs) / 1_000_000
        if abs(self.durationMs - expected_ms) > 1:
            raise ValueError(f"durationMs({self.durationMs})가 실제 구간({expected_ms:.1f}ms)과 일치하지 않습니다.")
        return self


class SensorSummary(BaseModel):
    pirMotion: bool
    pirLastMotionMs: int = Field(ge=0)
    tofDistanceMm: int = Field(ge=0)
    tofChangeMm: int
    tofStableMs: int = Field(ge=0)
    csi: CsiSummary


class FallAnalyzeRequest(BaseModel):
    type: Literal["event.candidate"] = "event.candidate"
    eventId: str
    timestamp: str
    deviceId: str
    roomId: str
    window: Optional[EventWindow] = None
    sensorSummary: SensorSummary
    localScore: float = Field(ge=0.0, le=1.0)
    localRiskLevel: Optional[RiskLevel] = None
    candidateReason: List[str] = Field(default_factory=list)


class VerificationPlan(BaseModel):
    required: bool
    method: VerificationMethod
    promptAsset: Optional[str] = None
    expectedOkText: List[str] = Field(default_factory=list)
    timeoutSec: int = Field(ge=0)


class FallAnalyzeResponse(BaseModel):
    type: Literal["analysis.result"] = "analysis.result"
    eventId: str
    timestamp: str
    isFall: bool
    confidence: float = Field(ge=0.0, le=1.0)
    riskLevel: RiskLevel
    recommendedAction: RecommendedAction
    situationSummary: str
    analysisReason: str
    verificationPlan: VerificationPlan
    analysisStatus: AnalysisStatus = "SUCCESS"


class VerificationRecord(BaseModel):
    method: VerificationMethod
    promptAsset: Optional[str] = None
    asked: bool
    userResponse: Optional[UserResponse] = None
    transcript: str = ""
    timeoutSec: int = Field(ge=0)


class NotificationPayload(BaseModel):
    channels: List[str] = Field(default_factory=list)
    message: str = ""


class NotificationRequest(BaseModel):
    type: Literal["notification.request"] = "notification.request"
    eventId: str
    timestamp: str
    deviceId: str
    roomId: str
    riskLevel: RiskLevel
    situationSummary: str
    escalationReason: str
    verification: VerificationRecord
    notification: NotificationPayload


class NotificationResult(BaseModel):
    type: Literal["notification.result"] = "notification.result"
    eventId: str
    timestamp: str
    notificationStatus: NotificationStatus
    channels: List[str] = Field(default_factory=list)
    attemptCount: int = Field(default=1, ge=0)
    error: Optional[str] = None


class OutcomeVerification(BaseModel):
    method: VerificationMethod
    promptAsset: Optional[str] = None
    asked: bool
    timeoutSec: int = Field(ge=0)


class OutcomeNotification(BaseModel):
    channels: List[str] = Field(default_factory=list)
    attemptCount: int = Field(default=0, ge=0)
    error: Optional[str] = None


class FallOutcomeRequest(BaseModel):
    type: Literal["response.outcome"] = "response.outcome"
    eventId: str
    timestamp: str
    recommendedAction: RecommendedAction
    userResponse: UserResponse
    transcript: str = ""
    verification: OutcomeVerification
    responseOutcome: ResponseOutcome
    notificationStatus: NotificationStatus
    notification: OutcomeNotification
