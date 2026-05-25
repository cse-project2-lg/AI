from typing import List, Literal, Optional

from pydantic import BaseModel, Field


RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
RecommendedAction = Literal["NO_ACTION", "OBSERVE", "VERIFY_USER", "NOTIFY_GUARDIAN"]
UserResponse = Literal["NOT_ASKED", "OK", "HELP", "NO_RESPONSE", "UNCLEAR"]
FinalState = Literal[
    "NORMAL",
    "OBSERVING",
    "CANCELED_BY_USER",
    "EMERGENCY_CONFIRMED",
    "NOTIFICATION_FAILED",
]


class SensorSummary(BaseModel):
    pirMotion: bool
    pirLastMotionMs: int = Field(ge=0)
    tofDistanceMm: int = Field(ge=0)
    tofChangeMm: int
    tofStableMs: int = Field(ge=0)
    csiChangeScore: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    csiPacketCount: Optional[int] = Field(default=None, ge=0)


class FallAnalyzeRequest(BaseModel):
    eventId: str
    timestamp: str
    deviceId: str
    roomId: str
    sensorSummary: SensorSummary
    localScore: float = Field(ge=0.0, le=1.0)


class FallAnalyzeResponse(BaseModel):
    eventId: str
    isFall: bool
    confidence: float = Field(ge=0.0, le=1.0)
    riskLevel: RiskLevel
    recommendedAction: RecommendedAction
    situationSummary: str
    reasoning: str
    verificationMessage: str = ""
    timeoutSec: int = Field(default=10, ge=0)


class NotificationResult(BaseModel):
    sent: bool
    channels: List[str]


class FallOutcomeRequest(BaseModel):
    eventId: str
    timestamp: str
    userResponse: UserResponse
    transcript: str = ""
    finalState: FinalState
    notification: NotificationResult
