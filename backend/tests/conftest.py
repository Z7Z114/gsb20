"""测试公共配置。

两个关键点：
1. 把仓库根目录放进 sys.path，使 `import backend.*` 在 `cd backend && pytest` 下可用；
2. 在任何 backend 模块被导入前把外部服务与数据目录指向临时位置，
   保证整套测试不联网、不读取真实密钥、不污染工作目录。
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

_TMP = tempfile.mkdtemp(prefix="iep-tests-")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "iep_test.db").replace("\\", "/")
os.environ["UPLOAD_DIR"] = os.path.join(_TMP, "uploads")
for _key in (
    "OPENAI_API_KEY",
    "PYANNOTE_AUTH_TOKEN",
    "SMTP_HOST",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "ENCRYPTION_KEY",
):
    os.environ.pop(_key, None)
