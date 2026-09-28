from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


class ChildBase(BaseModel):
    name: str
    age: Optional[int] = None
    diagnosis: Optional[str] = None


class ChildCreate(ChildBase):
    pass


class Child(ChildBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TeamMemberBase(BaseModel):
    name: str
    role: str
    email: EmailStr


class TeamMemberCreate(TeamMemberBase):
    pass


class TeamMember(TeamMemberBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BehaviorRecordBase(BaseModel):
    child_id: int
    behavior_type: str
    frequency: float
    intensity: Optional[int] = None
    duration: Optional[float] = None
    notes: Optional[str] = None
    target_behavior: bool = False
    recorded_at: Optional[datetime] = None


class BehaviorRecordCreate(BehaviorRecordBase):
    pass


class BehaviorRecord(BehaviorRecordBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MeetingBase(BaseModel):
    child_id: int
    title: str
    date: Optional[datetime] = None


class MeetingCreate(MeetingBase):
    participant_ids: List[int] = []


class Meeting(MeetingBase):
    id: int
    status: str
    transcript: Optional[str] = None
    iep_summary: Optional[str] = None
    suggestions: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TranscriptSegmentBase(BaseModel):
    meeting_id: int
    speaker: str
    speaker_role: Optional[str] = None
    start_time: float
    end_time: float
    text: str


class TranscriptSegmentCreate(TranscriptSegmentBase):
    pass


class TranscriptSegment(TranscriptSegmentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MeetingProcessRequest(BaseModel):
    meeting_id: int


class BehaviorChartData(BaseModel):
    date: str
    behavior_type: str
    frequency: float
    intensity: Optional[float] = None


class IEPSummaryResponse(BaseModel):
    meeting_id: int
    child_name: str
    meeting_date: datetime
    summary: str
    suggestions: str
    target_behaviors: List[str]
    intervention_strategies: List[str]
    progress_notes: str
