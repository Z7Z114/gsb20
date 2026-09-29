"""行为规格回归测试：逐条对应 README「行为规格」的验收点。

这些用例在未修复的实现上应当失败，修复后通过。
"""
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    import main as app_module

    with TestClient(app_module.app) as test_client:
        yield test_client


def create_child(client, name="规格儿童"):
    resp = client.post("/api/core/children", json={"name": name, "age": 6, "diagnosis": "ASD"})
    assert resp.status_code == 200, resp.text
    return resp.json()


def create_member(client, name, role, email):
    resp = client.post("/api/core/team-members", json={"name": name, "role": role, "email": email})
    assert resp.status_code == 200, resp.text
    return resp.json()


def create_meeting(client, child_id, participant_ids=(), title="规格会议"):
    resp = client.post(
        "/api/core/meetings",
        json={"child_id": child_id, "title": title, "participant_ids": list(participant_ids)},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def upload_audio(client, meeting_id, filename="session.wav"):
    resp = client.post(
        f"/api/processing/upload-audio/{meeting_id}",
        files={"file": (filename, b"RIFF....WAVEfmt offline", "audio/wav")},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------- A. 行为记录与会议完整性 ----------

def test_a1_a2_a3_behavior_record_create_and_list(client):
    child = create_child(client, name="行为记录儿童")

    resp = client.post(
        "/api/core/behavior-records",
        json={"child_id": child["id"], "behavior_type": "哭闹", "frequency": 3},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"]
    assert body["created_at"]
    assert body["recorded_at"]

    resp2 = client.post(
        "/api/core/behavior-records",
        json={
            "child_id": child["id"],
            "behavior_type": "自伤",
            "frequency": 1,
            "recorded_at": "2020-01-15T10:30:00",
        },
    )
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["recorded_at"].startswith("2020-01-15T10:30:00")
    assert resp2.json()["created_at"]

    listed = client.get(f"/api/core/behavior-records/{child['id']}")
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) == 2
    assert all("created_at" in item for item in items)
    recorded_times = [item["recorded_at"] for item in items]
    assert recorded_times == sorted(recorded_times, reverse=True)


def test_a4_meeting_rejects_dangling_references(client):
    child = create_child(client, name="校验儿童")
    member = create_member(client, "校验成员", "医生", "check@example.com")

    bad_child = client.post(
        "/api/core/meetings",
        json={"child_id": 999999, "title": "坏儿童", "participant_ids": []},
    )
    assert bad_child.status_code == 404

    bad_member = client.post(
        "/api/core/meetings",
        json={"child_id": child["id"], "title": "坏成员", "participant_ids": [member["id"], 999999]},
    )
    assert bad_member.status_code == 404

    meetings = client.get("/api/core/meetings", params={"child_id": child["id"]}).json()
    assert meetings == []


# ---------- B. 行为图表数据 ----------

def test_b2_chart_preserves_zero_intensity_and_frequency(client):
    child = create_child(client, name="零值儿童")
    client.post(
        "/api/core/behavior-records",
        json={
            "child_id": child["id"],
            "behavior_type": "哭闹",
            "frequency": 0,
            "intensity": 0,
            "recorded_at": "2021-01-01T08:00:00",
        },
    )
    client.post(
        "/api/core/behavior-records",
        json={
            "child_id": child["id"],
            "behavior_type": "尖叫",
            "frequency": 2,
            "recorded_at": "2021-01-02T08:00:00",
        },
    )

    chart = client.get(f"/api/core/behavior-records/chart/{child['id']}")
    assert chart.status_code == 200
    rows = chart.json()
    assert len(rows) == 2
    assert rows[0]["date"] == "2021-01-01"
    assert rows[0]["intensity"] == 0.0
    assert rows[0]["frequency"] == 0.0
    assert rows[1]["date"] == "2021-01-02"
    assert rows[1]["intensity"] is None


# ---------- C. 音频上传 ----------

def test_c1_upload_filename_cannot_escape_upload_dir(client):
    child = create_child(client, name="上传安全儿童")
    meeting = create_meeting(client, child["id"], title="路径穿越会议")

    upload_root = os.path.abspath(os.environ["UPLOAD_DIR"])
    for evil_name in ("../../../evil.txt", "..\\..\\evil2.txt", "/tmp/abs.txt"):
        resp = client.post(
            f"/api/processing/upload-audio/{meeting['id']}",
            files={"file": (evil_name, b"payload", "application/octet-stream")},
        )
        assert resp.status_code == 200, resp.text
        stored = os.path.abspath(resp.json()["file_path"])
        assert os.path.commonpath([upload_root, stored]) == upload_root
        assert os.path.exists(stored)


def test_c3_upload_missing_meeting_returns_404(client):
    resp = client.post(
        "/api/processing/upload-audio/999999",
        files={"file": ("a.wav", b"x", "audio/wav")},
    )
    assert resp.status_code == 404


# ---------- D. 会议处理（离线） ----------

def _prepare_processable_meeting(client, suffix=""):
    child = create_child(client, name=f"处理儿童{suffix}")
    member = create_member(client, f"处理成员{suffix}", "语言治疗师", f"proc{suffix}@example.com")
    meeting = create_meeting(client, child["id"], [member["id"]], title=f"处理会议{suffix}")
    client.post(
        "/api/core/behavior-records",
        json={
            "child_id": child["id"],
            "behavior_type": "自伤行为",
            "frequency": 4,
            "intensity": 2,
            "target_behavior": True,
        },
    )
    client.post(
        "/api/core/behavior-records",
        json={"child_id": child["id"], "behavior_type": "哭闹", "frequency": 2},
    )
    upload_audio(client, meeting["id"])
    return child, member, meeting


def test_d1_d3_offline_processing_completes_with_summary(client):
    child, _, meeting = _prepare_processable_meeting(client, suffix="D1")

    resp = client.post(f"/api/processing/process-meeting/{meeting['id']}")
    assert resp.status_code == 200, resp.text

    status = client.get(f"/api/processing/meeting-status/{meeting['id']}").json()
    assert status["status"] == "completed"
    assert status["has_summary"] is True
    assert status["has_transcript"] is True

    summary = client.get(f"/api/processing/iep-summary/{meeting['id']}").json()
    assert summary["summary"].strip()
    assert isinstance(summary["target_behaviors"], list) and summary["target_behaviors"]
    assert "自伤行为" in summary["target_behaviors"]
    assert isinstance(summary["intervention_strategies"], list) and summary["intervention_strategies"]
    assert isinstance(summary["suggestions"], list) and summary["suggestions"]

    detail = client.get(f"/api/core/meetings/{meeting['id']}").json()
    assert detail["status"] == "completed"
    assert detail["iep_summary"]


def test_d4_reprocessing_is_idempotent(client):
    _, _, meeting = _prepare_processable_meeting(client, suffix="D4")

    assert client.post(f"/api/processing/process-meeting/{meeting['id']}").status_code == 200
    first = client.get(f"/api/core/meetings/{meeting['id']}/transcripts").json()
    assert len(first) > 0
    first_summary = client.get(f"/api/processing/iep-summary/{meeting['id']}").json()["summary"]

    assert client.post(f"/api/processing/process-meeting/{meeting['id']}").status_code == 200
    second = client.get(f"/api/core/meetings/{meeting['id']}/transcripts").json()
    assert len(second) == len(first)

    second_summary = client.get(f"/api/processing/iep-summary/{meeting['id']}").json()["summary"]
    assert second_summary == first_summary


def test_d2_empty_summary_marks_failed(client, monkeypatch):
    from backend.routers import processing_router

    monkeypatch.setattr(
        processing_router.iep_summarizer,
        "generate_iep_summary",
        lambda *args, **kwargs: {"full_summary": "", "structured_data": {}},
    )

    _, _, meeting = _prepare_processable_meeting(client, suffix="D2")
    assert client.post(f"/api/processing/process-meeting/{meeting['id']}").status_code == 200

    status = client.get(f"/api/processing/meeting-status/{meeting['id']}").json()
    assert status["status"] == "failed"
    detail = client.get(f"/api/core/meetings/{meeting['id']}").json()
    assert not detail["iep_summary"]
    transcripts = client.get(f"/api/core/meetings/{meeting['id']}/transcripts").json()
    assert transcripts == []


def test_d5_processing_failure_leaves_no_partial_data(client, monkeypatch):
    from backend.routers import processing_router

    def boom(_path):
        raise RuntimeError("模拟音频处理失败")

    monkeypatch.setattr(processing_router.audio_processor, "process_meeting_audio", boom)

    _, _, meeting = _prepare_processable_meeting(client, suffix="D5")
    assert client.post(f"/api/processing/process-meeting/{meeting['id']}").status_code == 200

    status = client.get(f"/api/processing/meeting-status/{meeting['id']}").json()
    assert status["status"] == "failed"
    assert status["has_transcript"] is False
    assert status["has_summary"] is False
    transcripts = client.get(f"/api/core/meetings/{meeting['id']}/transcripts").json()
    assert transcripts == []


def test_d5_process_meeting_not_found_and_no_audio(client):
    assert client.post("/api/processing/process-meeting/999999").status_code == 404

    child = create_child(client, name="无音频儿童")
    meeting = create_meeting(client, child["id"], title="无音频会议")
    assert client.post(f"/api/processing/process-meeting/{meeting['id']}").status_code == 400


# ---------- E. 加密与邮件 ----------

class _FakeSMTP:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self):
        pass

    def login(self, *args):
        pass

    def sendmail(self, sender, recipient, text):
        if recipient.startswith("fail"):
            raise RuntimeError("模拟 SMTP 发送失败")


def test_e1_encryption_key_actually_decrypts(monkeypatch):
    from cryptography.fernet import Fernet
    from backend.services import email_service as email_module
    from backend.services.email_service import EmailService

    monkeypatch.setattr(email_module.smtplib, "SMTP", _FakeSMTP)

    service = EmailService()
    ciphertext = service.encrypt_content("机密会议纪要")

    result = service.send_iep_email(["ok@example.com"], "主题", "正文内容")
    key = result["encryption_key"]
    assert isinstance(key, str)
    assert len(key) == 44
    decrypted = Fernet(key.encode("utf-8")).decrypt(ciphertext.encode("utf-8"))
    assert decrypted.decode("utf-8") == "机密会议纪要"
    assert result["success"] == ["ok@example.com"]


def test_e2_only_successful_recipients_recorded(client, monkeypatch):
    from backend.database import SessionLocal
    from backend.models import SentEmail
    from backend.services import email_service as email_module

    monkeypatch.setattr(email_module.smtplib, "SMTP", _FakeSMTP)

    child = create_child(client, name="邮件儿童E2")
    ok_member = create_member(client, "成功收件人", "家长", "ok-e2@example.com")
    fail_member = create_member(client, "失败收件人", "医生", "fail-e2@example.com")
    meeting = create_meeting(client, child["id"], [ok_member["id"], fail_member["id"]], title="邮件会议E2")
    upload_audio(client, meeting["id"])
    assert client.post(f"/api/processing/process-meeting/{meeting['id']}").status_code == 200

    resp = client.post(f"/api/processing/send-email/{meeting['id']}")
    assert resp.status_code == 200, resp.text
    email_result = resp.json()["email_result"]
    assert email_result["success"] == ["ok-e2@example.com"]
    assert [f["email"] for f in email_result["failed"]] == ["fail-e2@example.com"]

    db = SessionLocal()
    try:
        rows = db.query(SentEmail).filter(SentEmail.meeting_id == meeting["id"]).all()
        assert sorted(row.recipient for row in rows) == ["ok-e2@example.com"]
    finally:
        db.close()


def test_e3_send_email_requires_completed_and_recipients(client):
    child = create_child(client, name="邮件儿童E3")
    meeting = create_meeting(client, child["id"], title="无参会人会议")
    upload_audio(client, meeting["id"])
    assert client.post(f"/api/processing/process-meeting/{meeting['id']}").status_code == 200
    status = client.get(f"/api/processing/meeting-status/{meeting['id']}").json()
    assert status["status"] == "completed"

    resp = client.post(f"/api/processing/send-email/{meeting['id']}")
    assert resp.status_code == 400
