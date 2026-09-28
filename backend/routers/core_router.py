from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models import Child, TeamMember, Meeting, BehaviorRecord, TranscriptSegment, MeetingParticipant
from backend.schemas import (
    ChildCreate, Child as ChildSchema,
    TeamMemberCreate, TeamMember as TeamMemberSchema,
    MeetingCreate, Meeting as MeetingSchema,
    BehaviorRecordCreate, BehaviorRecord as BehaviorRecordSchema,
    TranscriptSegmentCreate, MeetingProcessRequest,
    BehaviorChartData, IEPSummaryResponse
)
from datetime import datetime

router = APIRouter(prefix="/api/core", tags=["Core"])


@router.post("/children", response_model=ChildSchema)
def create_child(child: ChildCreate, db: Session = Depends(get_db)):
    db_child = Child(**child.dict())
    db.add(db_child)
    db.commit()
    db.refresh(db_child)
    return db_child


@router.get("/children", response_model=List[ChildSchema])
def get_children(db: Session = Depends(get_db)):
    return db.query(Child).all()


@router.get("/children/{child_id}", response_model=ChildSchema)
def get_child(child_id: int, db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    return child


@router.post("/team-members", response_model=TeamMemberSchema)
def create_team_member(member: TeamMemberCreate, db: Session = Depends(get_db)):
    db_member = TeamMember(**member.dict())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


@router.get("/team-members", response_model=List[TeamMemberSchema])
def get_team_members(db: Session = Depends(get_db)):
    return db.query(TeamMember).all()


@router.post("/meetings", response_model=MeetingSchema)
def create_meeting(meeting: MeetingCreate, db: Session = Depends(get_db)):
    db_meeting = Meeting(
        child_id=meeting.child_id,
        title=meeting.title,
        date=meeting.date or datetime.utcnow()
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)

    for member_id in meeting.participant_ids:
        participant = MeetingParticipant(
            meeting_id=db_meeting.id,
            team_member_id=member_id
        )
        db.add(participant)

    db.commit()
    return db_meeting


@router.get("/meetings", response_model=List[MeetingSchema])
def get_meetings(child_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Meeting)
    if child_id:
        query = query.filter(Meeting.child_id == child_id)
    return query.all()


@router.get("/meetings/{meeting_id}", response_model=MeetingSchema)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.post("/behavior-records", response_model=BehaviorRecordSchema)
def create_behavior_record(record: BehaviorRecordCreate, db: Session = Depends(get_db)):
    db_record = BehaviorRecord(
        **record.dict(exclude_unset=True),
        recorded_at=record.recorded_at or datetime.utcnow()
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.get("/behavior-records/chart/{child_id}", response_model=List[BehaviorChartData])
def get_behavior_chart_data(child_id: int, db: Session = Depends(get_db)):
    records = db.query(BehaviorRecord).filter(
        BehaviorRecord.child_id == child_id
    ).order_by(BehaviorRecord.recorded_at).all()

    chart_data = []
    for record in records:
        chart_data.append(BehaviorChartData(
            date=record.recorded_at.strftime("%Y-%m-%d") if record.recorded_at else "",
            behavior_type=record.behavior_type,
            frequency=record.frequency,
            intensity=float(record.intensity) if record.intensity else None
        ))

    return chart_data


@router.get("/behavior-records/{child_id}", response_model=List[BehaviorRecordSchema])
def get_behavior_records(child_id: int, db: Session = Depends(get_db)):
    return db.query(BehaviorRecord).filter(
        BehaviorRecord.child_id == child_id
    ).order_by(BehaviorRecord.recorded_at.desc()).all()


@router.get("/meetings/{meeting_id}/participants")
def get_meeting_participants(meeting_id: int, db: Session = Depends(get_db)):
    participants = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id
    ).all()

    result = []
    for p in participants:
        member = db.query(TeamMember).filter(TeamMember.id == p.team_member_id).first()
        if member:
            result.append({
                "id": member.id,
                "name": member.name,
                "role": member.role,
                "email": member.email,
                "role_in_meeting": p.role_in_meeting
            })

    return result


@router.get("/meetings/{meeting_id}/transcripts")
def get_meeting_transcripts(meeting_id: int, db: Session = Depends(get_db)):
    segments = db.query(TranscriptSegment).filter(
        TranscriptSegment.meeting_id == meeting_id
    ).order_by(TranscriptSegment.start_time).all()

    return [
        {
            "id": s.id,
            "speaker": s.speaker,
            "speaker_role": s.speaker_role,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "text": s.text
        }
        for s in segments
    ]
