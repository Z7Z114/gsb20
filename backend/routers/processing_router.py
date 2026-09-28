from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
import os
import json
from datetime import datetime
from backend.database import get_db
from backend.models import Meeting, Child, TeamMember, BehaviorRecord, TranscriptSegment, SentEmail, MeetingParticipant
from backend.services.audio_service import audio_processor
from backend.services.iep_service import iep_summarizer
from backend.services.email_service import email_service

router = APIRouter(prefix="/api/processing", tags=["Processing"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-audio/{meeting_id}")
async def upload_audio(meeting_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    file_location = os.path.join(UPLOAD_DIR, f"meeting_{meeting_id}_{file.filename}")

    with open(file_location, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    meeting.audio_file_path = file_location
    meeting.status = "audio_uploaded"
    db.commit()

    return {
        "success": True,
        "message": "Audio uploaded successfully",
        "file_path": file_location
    }


@router.post("/process-meeting/{meeting_id}")
async def process_meeting(meeting_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not meeting.audio_file_path or not os.path.exists(meeting.audio_file_path):
        raise HTTPException(status_code=400, detail="Audio file not found")

    meeting.status = "processing"
    db.commit()

    background_tasks.add_task(process_meeting_background, meeting_id, db)

    return {
        "success": True,
        "message": "Meeting processing started in background",
        "meeting_id": meeting_id
    }


def process_meeting_background(meeting_id: int, db):
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return

        print(f"[{datetime.now()}] Starting processing for meeting {meeting_id}")

        audio_result = audio_processor.process_meeting_audio(meeting.audio_file_path)

        meeting.transcript = audio_result["full_transcript"]
        meeting.diarization_result = json.dumps(audio_result["diarization"], ensure_ascii=False)
        db.commit()

        print(f"[{datetime.now()}] Audio processing completed for meeting {meeting_id}")

        participants = db.query(MeetingParticipant).filter(
            MeetingParticipant.meeting_id == meeting_id
        ).all()

        team_members = []
        for p in participants:
            member = db.query(TeamMember).filter(TeamMember.id == p.team_member_id).first()
            if member:
                team_members.append({
                    "id": member.id,
                    "name": member.name,
                    "role": member.role
                })

        merged_segments = audio_result["merged_segments"]
        if team_members:
            merged_segments = iep_summarizer.identify_speaker_roles(
                merged_segments, team_members
            )

        for seg in merged_segments:
            transcript_seg = TranscriptSegment(
                meeting_id=meeting_id,
                speaker=seg.get("speaker_name", seg["speaker"]),
                speaker_role=seg.get("speaker_role", ""),
                start_time=seg["start"],
                end_time=seg["end"],
                text=seg["text"]
            )
            db.add(transcript_seg)

        db.commit()

        print(f"[{datetime.now()}] Speaker identification completed for meeting {meeting_id}")

        child = db.query(Child).filter(Child.id == meeting.child_id).first()
        child_info = {
            "name": child.name,
            "age": child.age,
            "diagnosis": child.diagnosis
        } if child else {}

        behavior_records = db.query(BehaviorRecord).filter(
            BehaviorRecord.child_id == meeting.child_id
        ).order_by(BehaviorRecord.recorded_at.desc()).limit(30).all()

        behavior_history = [
            {
                "behavior_type": r.behavior_type,
                "frequency": r.frequency,
                "intensity": r.intensity,
                "duration": r.duration,
                "recorded_at": r.recorded_at.strftime("%Y-%m-%d") if r.recorded_at else "",
                "notes": r.notes,
                "target_behavior": r.target_behavior
            }
            for r in behavior_records
        ]

        iep_result = iep_summarizer.generate_iep_summary(
            audio_result["full_transcript"],
            child_info,
            behavior_history
        )

        meeting.iep_summary = iep_result["full_summary"]
        meeting.suggestions = json.dumps(iep_result["structured_data"], ensure_ascii=False)
        meeting.status = "completed"
        db.commit()

        print(f"[{datetime.now()}] IEP summary generated for meeting {meeting_id}")

    except Exception as e:
        print(f"[{datetime.now()}] Error processing meeting {meeting_id}: {str(e)}")
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting:
            meeting.status = "failed"
            db.commit()


@router.post("/send-email/{meeting_id}")
async def send_meeting_email(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if meeting.status != "completed":
        raise HTTPException(status_code=400, detail="Meeting processing not completed")

    participants = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id
    ).all()

    recipients = []
    participant_info = []
    for p in participants:
        member = db.query(TeamMember).filter(TeamMember.id == p.team_member_id).first()
        if member:
            recipients.append(member.email)
            participant_info.append({
                "name": member.name,
                "role": member.role,
                "email": member.email
            })

    if not recipients:
        raise HTTPException(status_code=400, detail="No recipients found")

    child = db.query(Child).filter(Child.id == meeting.child_id).first()
    child_info = {
        "name": child.name,
        "age": child.age,
        "diagnosis": child.diagnosis
    } if child else {}

    behavior_records = db.query(BehaviorRecord).filter(
        BehaviorRecord.child_id == meeting.child_id
    ).order_by(BehaviorRecord.recorded_at.desc()).limit(10).all()

    behavior_list = [
        {
            "behavior_type": r.behavior_type,
            "frequency": r.frequency,
            "intensity": r.intensity,
            "duration": r.duration,
            "recorded_at": r.recorded_at,
            "notes": r.notes
        }
        for r in behavior_records
    ]

    meeting_info = {
        "title": meeting.title,
        "date": meeting.date
    }

    markdown_content = email_service.generate_iep_markdown(
        child_info,
        meeting_info,
        meeting.iep_summary,
        behavior_list,
        participant_info
    )

    meeting_data = {
        "meeting_id": meeting_id,
        "child": child_info,
        "participants": participant_info,
        "iep_summary": meeting.iep_summary,
        "suggestions": meeting.suggestions
    }

    subject = f"[IEP会议纪要] {child.name if child else '儿童'} - {meeting.date.strftime('%Y-%m-%d') if meeting.date else ''}"

    email_result = email_service.send_iep_email(
        recipients,
        subject,
        markdown_content,
        meeting.transcript,
        meeting_data
    )

    for recipient in recipients:
        sent_email = SentEmail(
            meeting_id=meeting_id,
            recipient=recipient,
            subject=subject,
            encrypted=True
        )
        db.add(sent_email)

    db.commit()

    return {
        "success": True,
        "email_result": email_result,
        "markdown_preview": markdown_content[:1000] + "..." if len(markdown_content) > 1000 else markdown_content
    }


@router.get("/meeting-status/{meeting_id}")
def get_meeting_status(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return {
        "meeting_id": meeting_id,
        "status": meeting.status,
        "has_transcript": bool(meeting.transcript),
        "has_summary": bool(meeting.iep_summary),
        "has_audio": bool(meeting.audio_file_path)
    }


@router.get("/iep-summary/{meeting_id}")
def get_iep_summary(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    child = db.query(Child).filter(Child.id == meeting.child_id).first()

    try:
        suggestions = json.loads(meeting.suggestions) if meeting.suggestions else {}
    except:
        suggestions = {}

    return {
        "meeting_id": meeting_id,
        "child_name": child.name if child else "",
        "meeting_date": meeting.date,
        "summary": meeting.iep_summary or "",
        "suggestions": suggestions.get("key_recommendations", []),
        "target_behaviors": suggestions.get("target_behaviors", []),
        "intervention_strategies": suggestions.get("intervention_strategies", []),
        "progress_notes": suggestions.get("progress_assessment", "")
    }
