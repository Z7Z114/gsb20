import os
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from dotenv import load_dotenv
from typing import List, Dict
from datetime import datetime

load_dotenv()


class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.encryption_key = self._get_encryption_key()

    def _get_encryption_key(self) -> bytes:
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            return Fernet.generate_key()

        if len(key) != 32:
            salt = b'autism_iep_salt'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        else:
            key = base64.urlsafe_b64encode(key.encode())

        return key

    def encrypt_content(self, content: str) -> str:
        fernet = Fernet(self.encryption_key)
        encrypted = fernet.encrypt(content.encode('utf-8'))
        return encrypted.decode('utf-8')

    def decrypt_content(self, encrypted_content: str) -> str:
        fernet = Fernet(self.encryption_key)
        decrypted = fernet.decrypt(encrypted_content.encode('utf-8'))
        return decrypted.decode('utf-8')

    def generate_iep_markdown(
        self,
        child_info: Dict,
        meeting_info: Dict,
        iep_summary: str,
        behavior_records: List[Dict],
        participants: List[Dict]
    ) -> str:
        date_str = meeting_info.get("date", datetime.now()).strftime("%Y年%m月%d日")

        md_content = f"""# 个别化教育计划(IEP)会议纪要

## 会议基本信息

**会议主题**: {meeting_info.get("title", "IEP团队会议")}
**会议日期**: {date_str}
**参会人员**:
{chr(10).join([f"- {p['name']} ({p['role']})" for p in participants])}

---

## 儿童基本信息

**姓名**: {child_info.get("name", "")}
**年龄**: {child_info.get("age", "")}岁
**诊断**: {child_info.get("diagnosis", "")}

---

## 会议内容摘要

{iep_summary}

---

## 行为记录数据

| 行为类型 | 发生频率 | 强度 | 持续时间(分钟) | 记录日期 | 备注 |
|----------|----------|------|----------------|----------|------|
"""

        for record in behavior_records:
            intensity = record.get("intensity", "")
            duration = record.get("duration", "")
            recorded_at = record.get("recorded_at", "")
            if hasattr(recorded_at, "strftime"):
                recorded_at = recorded_at.strftime("%Y-%m-%d")
            notes = record.get("notes", "")

            md_content += f"| {record.get('behavior_type', '')} | {record.get('frequency', '')} | {intensity} | {duration} | {recorded_at} | {notes} |\n"

        md_content += f"""
---

## 附件说明

本邮件包含加密的会议完整记录和IEP文档。
请使用团队共享的解密密钥查看完整内容。

---

*此邮件由IEP会议管理系统自动生成*
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

        return md_content

    def send_iep_email(
        self,
        recipients: List[str],
        subject: str,
        markdown_content: str,
        full_transcript: str = "",
        meeting_data: Dict = None
    ) -> Dict:
        results = {"success": [], "failed": [], "encryption_key": None}

        try:
            encrypted_md = self.encrypt_content(markdown_content)
            encrypted_transcript = self.encrypt_content(full_transcript) if full_transcript else ""
            key_for_recipient = self.encryption_key.decode('utf-8')
            results["encryption_key"] = key_for_recipient

        except Exception as e:
            results["error"] = f"加密失败: {str(e)}"
            return results

        for recipient in recipients:
            try:
                msg = MIMEMultipart()
                msg['From'] = self.smtp_user
                msg['To'] = recipient
                msg['Subject'] = subject

                body = f"""您好，

附件是本次IEP会议的纪要文档。文档已加密，请使用以下密钥解密：

解密密钥: {key_for_recipient}

解密步骤：
1. 保存附件的.enc文件
2. 使用提供的解密工具或在线解密工具
3. 输入上述密钥获取完整的Markdown格式报告

如有任何问题，请联系IEP协调员。

此致
敬礼
IEP会议管理系统
"""

                msg.attach(MIMEText(body, 'plain', 'utf-8'))

                md_filename = f"IEP_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md.enc"
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(encrypted_md.encode('utf-8'))
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {md_filename}')
                msg.attach(part)

                if encrypted_transcript:
                    transcript_filename = f"Meeting_Transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt.enc"
                    part2 = MIMEBase('application', 'octet-stream')
                    part2.set_payload(encrypted_transcript.encode('utf-8'))
                    encoders.encode_base64(part2)
                    part2.add_header('Content-Disposition', f'attachment; filename= {transcript_filename}')
                    msg.attach(part2)

                if meeting_data:
                    data_filename = f"Meeting_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json.enc"
                    encrypted_data = self.encrypt_content(json.dumps(meeting_data, ensure_ascii=False, indent=2))
                    part3 = MIMEBase('application', 'octet-stream')
                    part3.set_payload(encrypted_data.encode('utf-8'))
                    encoders.encode_base64(part3)
                    part3.add_header('Content-Disposition', f'attachment; filename= {data_filename}')
                    msg.attach(part3)

                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    text = msg.as_string()
                    server.sendmail(self.smtp_user, recipient, text)

                results["success"].append(recipient)

            except Exception as e:
                results["failed"].append({"email": recipient, "error": str(e)})

        return results


email_service = EmailService()
