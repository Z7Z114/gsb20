# 自闭症儿童干预 IEP 会议管理系统

一个全栈应用，用于管理自闭症儿童干预团队会议：登记儿童与团队成员、记录目标行为数据并绘制
趋势图、上传会议录音并转写、区分说话人、生成个别化教育计划（IEP）进展与调整建议，
最后把加密后的纪要邮件发送给全部参会人员。

- 后端：FastAPI + SQLAlchemy + SQLite（`backend/`，入口 `main.py`）
- 前端：React 18 + TypeScript + Vite + Tailwind + Recharts（`frontend/`）

## 功能特性

- **音频处理**：Whisper 语音转写 + pyannote 说话人区分（两者均为可选重型依赖）
- **AI 智能分析**：OpenAI 生成结构化 IEP 摘要、目标行为分析、干预策略评估与调整建议
- **数据可视化**：行为频率趋势图与行为类型统计图
- **安全通讯**：Fernet（AES-128-CBC + HMAC，即常说的 AES-256 强度方案）加密纪要，加密邮件投递

## 项目结构

```
.
├── main.py                     # FastAPI 入口（uvicorn main:app）
├── requirements.txt            # 轻量依赖（可离线跑测试）
├── requirements-ml.txt         # 可选重型依赖（Whisper / pyannote / torch）
├── backend/
│   ├── database.py             # 数据库引擎与会话
│   ├── models.py               # SQLAlchemy 模型
│   ├── schemas.py              # Pydantic 请求/响应模型
│   ├── routers/
│   │   ├── core_router.py      # 核心 CRUD 与图表
│   │   └── processing_router.py# 上传 / 处理 / 摘要 / 邮件
│   ├── services/
│   │   ├── audio_service.py    # 转写与说话人区分
│   │   ├── iep_service.py      # IEP 摘要生成
│   │   └── email_service.py    # 加密与邮件投递
│   └── tests/                  # 冒烟测试
└── frontend/                   # React 前端
```

## 快速开始

```bash
pip install -r requirements.txt          # 轻量依赖；重型语音依赖见 requirements-ml.txt
cp .env.example .env                     # 全部留空即可离线运行
uvicorn main:app --reload --port 8000    # 后端
cd frontend && npm install && npm run dev  # 前端（http://localhost:3000）
```

`OPENAI_API_KEY` / `PYANNOTE_AUTH_TOKEN` / `SMTP_*` 全部留空时，后端走离线分支：
不联网、不加载模型，也仍能把一次会议处理成可读的纪要。

## API 端点

### 核心 API（`/api/core`）
- `GET/POST /children`、`GET /children/{id}`
- `GET/POST /team-members`
- `GET/POST /meetings`、`GET /meetings/{id}`
- `GET /meetings/{id}/participants`、`GET /meetings/{id}/transcripts`
- `GET/POST /behavior-records`
- `GET /behavior-records/{child_id}`、`GET /behavior-records/chart/{child_id}`

### 处理 API（`/api/processing`）
- `POST /upload-audio/{meeting_id}`
- `POST /process-meeting/{meeting_id}`
- `POST /send-email/{meeting_id}`
- `GET /meeting-status/{meeting_id}`、`GET /iep-summary/{meeting_id}`

## 行为规格（验收标准）

以下是本系统的验收标准，与实现不一致的一律视为缺陷。所有接口在缺少必填字段或字段类型非法时
必须返回 4xx 而不是 500；资源不存在统一返回 404。

### A. 行为记录与会议完整性
- **A1** `POST /api/core/behavior-records` 成功后返回 200，响应体必须包含 `id`、`created_at`
  等字段；`GET /api/core/behavior-records/{child_id}` 同样返回含 `created_at` 的记录列表。
- **A2** `POST /api/core/behavior-records` 允许显式传入 `recorded_at`：传入时以该时间落库，
  不传时使用当前时间；两种写法都必须成功，不得 500。
- **A3** `GET /api/core/behavior-records/{child_id}` 按 `recorded_at` 倒序返回该儿童的记录。
- **A4** `POST /api/core/meetings` 的 `child_id` 必须指向已存在的儿童，`participant_ids` 中
  每个 id 必须指向已存在的团队成员；否则返回 404，不得创建出悬挂引用的会议。
- **A5** `POST /api/core/meetings` 成功后返回 200 且 `status` 为 `pending`，
  `GET /api/core/meetings/{id}/participants` 返回的成员与提交的 `participant_ids` 一致。

### B. 行为图表数据
- **B1** `GET /api/core/behavior-records/chart/{child_id}` 按 `recorded_at` 升序返回，
  每条记录一行，字段为 `date`（`YYYY-MM-DD`）、`behavior_type`、`frequency`、`intensity`。
- **B2** `intensity` 为 `0` 时必须原样返回 `0.0`，不得因为 0 是假值而变成 `null`；
  只有 `intensity` 确实为空时才返回 `null`。`frequency` 同理（`0` 也要保留）。

### C. 音频上传
- **C1** 上传目录由环境变量 `UPLOAD_DIR` 指定（缺省 `uploads`）。无论客户端提交的
  `filename` 含 `..` 还是路径分隔符，最终落盘文件都必须严格位于该上传目录内，不得逃逸。
- **C2** 上传成功后 `file_path` 指向真实存在的文件，且该会议的 `status` 变为 `audio_uploaded`，
  `GET /api/processing/meeting-status/{id}` 的 `has_audio` 为 `true`。
- **C3** 会议不存在时上传返回 404。

### D. 会议处理（离线可验收）
- **D1** 未配置 `OPENAI_API_KEY` / 未安装模型时，处理必须走**确定性离线分支**：
  `POST /api/processing/process-meeting/{id}` 结束后会议 `status` 为 `completed`，
  且 `iep_summary` 非空；`GET /api/processing/iep-summary/{id}` 的 `summary` 非空，
  `target_behaviors`、`intervention_strategies`、`suggestions` 均为数组。
  离线分支不得联网、不得抛异常。
- **D2** 任何情况下都不得出现「`status` 为 `completed` 但 `iep_summary` 为空」的会议；
  若摘要确实无法生成，状态必须是 `failed`，且不得把空摘要写进去。
- **D3** 离线摘要应当是确定性的：同一份输入重复生成得到相同的 `summary` 与结构化字段；
  其中 `target_behaviors` 取自行为历史里 `target_behavior` 为真的行为类型（去重、保序）。
- **D4** 重复处理同一会议必须幂等：`POST /api/processing/process-meeting/{id}` 调用两次后，
  该会议的 `TranscriptSegment` 数量与只处理一次相同，不得翻倍。
- **D5** 未安装 Whisper / pyannote 时，处理必须优雅失败：会议 `status` 变为 `failed`，
  不得写入半截 transcript 或空摘要。会议不存在返回 404；会议没有音频返回 400。

### E. 加密与邮件
- **E1** `EmailService.send_iep_email` 返回的 `encryption_key` 必须是一个能被
  `cryptography.fernet.Fernet` 直接接受的密钥（32 字节 urlsafe base64，44 字符），
  并且用它能解密出该服务生成的密文——收件人拿到的密钥必须是可用的。
- **E2** `POST /api/processing/send-email/{id}` 只对**发送成功**的收件人写入 `SentEmail`；
  发送失败的收件人不得记为已发送。返回体需分别给出成功与失败的收件人。
- **E3** 会议 `status` 不是 `completed` 时发送邮件返回 400；没有任何参会人员时返回 400。

## 变更说明

本轮修复以「行为规格」为验收标准，逐条对齐实现，根因与修法如下：

1. **行为记录写接口 500（A1/A2）**
   - 根因一：`BehaviorRecord` 模型缺少 `created_at` 列，而响应模型要求该字段，
     响应校验失败导致 500。修法：模型补上 `created_at` 列。
   - 根因二：创建时用 `record.dict(exclude_unset=True)` 展开后又显式传
     `recorded_at=`，客户端显式提交 `recorded_at` 时同一关键字传两次抛
     `TypeError`。修法：展开时 `exclude={"recorded_at"}`，再统一按
     「显式传入优先、否则当前时间」落库。
2. **会议创建产生悬挂引用（A4）**
   - 根因：创建会议前未校验 `child_id` 与 `participant_ids` 是否存在。
     修法：先查儿童与每个团队成员，任一不存在即返回 404，且不写入任何数据。
3. **图表中 `intensity` 为 0 变成 `null`（B2）**
   - 根因：`if record.intensity` 把 `0` 当假值丢弃。修法：改为
     `is not None` 判断，`0` 原样返回 `0.0`，只有真正未记录才是 `null`。
4. **上传文件名路径穿越（C1）**
   - 根因：客户端 `filename` 直接拼进落盘路径。修法：统一把 `\` 视为分隔符后
     取 `os.path.basename`，空名回退为 `audio.bin`，落盘前用
     `os.path.commonpath` 校验绝对路径必须位于 `UPLOAD_DIR` 内，否则 400。
5. **离线处理「完成但摘要空白」（D1/D2/D3/D5）**
   - 根因一：未配置 Key 时 `IEPSummarizer.client` 为 `None`，OpenAI 调用抛异常
     被吞掉后返回空摘要，而路由层不看内容直接写库并置 `completed`。
     修法：新增确定性离线摘要分支（`target_behaviors` 取自行为历史中
     `target_behavior` 为真的类型，去重保序；干预策略/建议均由行为数据确定性
     推导，不联网、不含随机与时间因素）；OpenAI 路径失败或返回空摘要时，
     路由层一律置 `failed` 且不写入空摘要，杜绝「completed 但摘要为空」。
   - 根因二：未安装 Whisper / pyannote 时音频处理直接抛错。修法：完全离线
     （未配置 `OPENAI_API_KEY` 与 `PYANNOTE_AUTH_TOKEN`）时使用确定性本地
     转写兜底，处理可完整走完；配置了在线令牌但依赖缺失则抛错，由后台任务
     捕获并置 `failed`。
   - 根因三：后台处理分多次提交，中途失败会留下半截 transcript。修法：所有
     产物（转写、片段、摘要、状态）合并为最后一次提交，异常时回滚并置
     `failed`，不留半截数据。
6. **重复处理导致转写片段翻倍（D4）**
   - 根因：每次处理都直接插入新 `TranscriptSegment`。修法：写入前先删除该会议
     的旧片段，重复处理结果与处理一次一致（离线分支下摘要也逐字节相同）。
7. **邮件解密密钥解不开附件（E1）**
   - 根因：把已是合法 Fernet 密钥的 `encryption_key` 又做了一次 base64 编码，
     收件人拿到的是「密钥的编码」而非密钥本身。修法：直接下发
     `encryption_key` 原文（44 字符 urlsafe base64），`Fernet(key)` 可解密附件。
8. **发送失败的收件人也被记为已发送（E2）**
   - 根因：无论 `send_iep_email` 结果如何都为全部收件人写 `SentEmail`。
     修法：只为 `email_result["success"]` 中的收件人写记录，响应体同时给出
     成功与失败列表。

回归测试：`backend/tests/test_behavior_spec.py` 逐条覆盖上述规格点，
在未修复的实现上失败、修复后通过；原冒烟测试 `test_smoke.py` 未改动且保持全绿。

## 安全说明

- 邮件附件使用 Fernet 对称加密，解密密钥随邮件单独下发给参会人。
- `ENCRYPTION_KEY` 留空时每次启动随机生成，重启后旧密文不可解；生产环境请固定配置。
- 音频与转写内容含儿童隐私信息，请妥善保管并按机构要求轮换密钥。

## 注意事项

- Whisper / pyannote 为可选重型依赖（见 `requirements-ml.txt`），未安装时走离线分支。
- 前端仅用于查看，题目范围内不需要改动前端。
