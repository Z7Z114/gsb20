from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class Child(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer)
    diagnosis = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    behavior_records = relationship("BehaviorRecord", back_populates="child")
    meetings = relationship("Meeting", back_populates="child")


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    email = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"))
    title = Column(String(200), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    audio_file_path = Column(String(500))
    transcript = Column(Text)
    diarization_result = Column(Text)
    iep_summary = Column(Text)
    suggestions = Column(Text)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    child = relationship("Child", back_populates="meetings")
    participants = relationship("MeetingParticipant", back_populates="meeting")


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    team_member_id = Column(Integer, ForeignKey("team_members.id"))
    role_in_meeting = Column(String(50))

    meeting = relationship("Meeting", back_populates="participants")
    team_member = relationship("TeamMember")


class BehaviorRecord(Base):
    __tablename__ = "behavior_records"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"))
    behavior_type = Column(String(100), nullable=False)
    frequency = Column(Float, nullable=False)
    intensity = Column(Integer)
    duration = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    target_behavior = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    child = relationship("Child", back_populates="behavior_records")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    speaker = Column(String(100))
    speaker_role = Column(String(50))
    start_time = Column(Float)
    end_time = Column(Float)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class SentEmail(Base):
    __tablename__ = "sent_emails"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    recipient = Column(String(200))
    subject = Column(String(300))
    sent_at = Column(DateTime, default=datetime.utcnow)
    encrypted = Column(Boolean, default=True)
