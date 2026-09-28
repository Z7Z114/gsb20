"""冒烟测试：只覆盖顺利路径。

这些用例在初始快照上全绿；它们不覆盖 README「行为规格」里的边界语义，
因此通过它们并不代表规格已被满足。
"""
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    import main as app_module

    with TestClient(app_module.app) as test_client:
        yield test_client


def create_child(client, name="小明"):
    resp = client.post("/api/core/children", json={"name": name, "age": 7, "diagnosis": "ASD"})
    assert resp.status_code == 200, resp.text
    return resp.json()


def create_member(client, name="张老师", role="语言治疗师", email="zhang@example.com"):
    resp = client.post(
        "/api/core/team-members", json={"name": name, "role": role, "email": email}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def create_meeting(client, child_id, participant_ids=(), title="IEP 例行会议"):
    resp = client.post(
        "/api/core/meetings",
        json={"child_id": child_id, "title": title, "participant_ids": list(participant_ids)},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_root_and_health(client):
    assert client.get("/").status_code == 200
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_child_and_team_member_flow(client):
    child = create_child(client, name="顺利路径儿童")
    member = create_member(client, name="顺利路径治疗师", email="ok@example.com")

    assert client.get("/api/core/children").status_code == 200
    assert client.get(f"/api/core/children/{child['id']}").json()["name"] == "顺利路径儿童"
    assert client.get("/api/core/team-members").status_code == 200
    assert member["email"] == "ok@example.com"


def test_meeting_flow_with_participants(client):
    child = create_child(client, name="会议儿童")
    member = create_member(client, name="会议医生", role="医生", email="doc@example.com")

    meeting = create_meeting(client, child["id"], [member["id"]], title="首次IEP会议")
    assert meeting["status"] == "pending"

    detail = client.get(f"/api/core/meetings/{meeting['id']}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "首次IEP会议"

    listed = client.get("/api/core/meetings", params={"child_id": child["id"]})
    assert listed.status_code == 200
    assert [m["id"] for m in listed.json()] == [meeting["id"]]

    participants = client.get(f"/api/core/meetings/{meeting['id']}/participants")
    assert participants.status_code == 200
    assert [p["email"] for p in participants.json()] == ["doc@example.com"]


def test_audio_upload_and_status(client):
    child = create_child(client, name="上传儿童")
    meeting = create_meeting(client, child["id"], title="带录音的会议")

    upload = client.post(
        f"/api/processing/upload-audio/{meeting['id']}",
        files={"file": ("session.wav", b"RIFF....WAVEfmt ", "audio/wav")},
    )
    assert upload.status_code == 200, upload.text
    stored = upload.json()["file_path"]
    assert os.path.exists(stored)

    status = client.get(f"/api/processing/meeting-status/{meeting['id']}")
    assert status.status_code == 200
    body = status.json()
    assert body["status"] == "audio_uploaded"
    assert body["has_audio"] is True
    assert body["has_transcript"] is False


def test_behavior_chart_and_empty_summary(client):
    child = create_child(client, name="图表儿童")
    meeting = create_meeting(client, child["id"], title="无摘要会议")

    chart = client.get(f"/api/core/behavior-records/chart/{child['id']}")
    assert chart.status_code == 200
    assert chart.json() == []

    summary = client.get(f"/api/processing/iep-summary/{meeting['id']}")
    assert summary.status_code == 200
    assert summary.json()["summary"] == ""
    assert summary.json()["target_behaviors"] == []


def test_send_email_requires_completed_meeting(client):
    child = create_child(client, name="邮件儿童")
    member = create_member(client, name="邮件家长", role="家长", email="parent@example.com")
    meeting = create_meeting(client, child["id"], [member["id"]], title="未完成会议")

    resp = client.post(f"/api/processing/send-email/{meeting['id']}")
    assert resp.status_code == 400
