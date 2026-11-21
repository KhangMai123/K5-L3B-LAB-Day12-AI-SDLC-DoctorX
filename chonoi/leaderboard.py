"""Mở rộng `leaderboard` (TICKET-04 mục 3): bảng xếp hạng cục bộ, top 10, lưu bền vững.

Store: {"entries": [{"name", "score", "days_completed", "seed"}, ...]} đã sắp sẵn.
Sắp điểm giảm dần; hòa thì mục ghi trước đứng trước (giữ nguyên khi mở lại vì store lưu đúng thứ tự).
File xếp hạng không ảnh hưởng JSONL; ghi qua file tạm cùng thư mục rồi thay thế nguyên tử.
"""

import json
import os
import tempfile

from .errors import BadInput

TOP = 10
DEFAULT_STORE = os.path.join(os.path.expanduser("~"), ".chonoi-doctorx", "leaderboard.json")


def validate_name(name):
    if not isinstance(name, str) or not name.strip():
        raise BadInput("--player-name phải là tên Unicode khác rỗng")
    return name


def _valid_entry(e):
    return (isinstance(e, dict) and set(e) == {"name", "score", "days_completed", "seed"}
            and isinstance(e["name"], str) and e["name"].strip()
            and all(isinstance(e[k], int) and not isinstance(e[k], bool) for k in ("score", "days_completed", "seed")))


def load(path):
    """Đọc store; chưa có file -> bảng rỗng. Sai schema -> BadInput (mã 2)."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được bảng xếp hạng {path}: {e}")
    if not isinstance(data, dict) or set(data) != {"entries"} or not isinstance(data["entries"], list):
        raise BadInput("bảng xếp hạng phải có đúng khóa 'entries' (mảng)")
    if not all(_valid_entry(e) for e in data["entries"]):
        raise BadInput("mục xếp hạng phải có name (khác rỗng), score, days_completed, seed (số nguyên)")
    return ranked(data["entries"])


def ranked(entries):
    # sorted() ổn định: hòa điểm giữ thứ tự ghi
    return sorted(entries, key=lambda e: -e["score"])[:TOP]


def _write(path, entries):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".lb-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"entries": entries}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def record(path, name, score, days_completed, seed):
    """Thêm một mục (sau mọi mục cùng điểm đã có), giữ top 10, lưu lại."""
    entries = load(path)
    entries.append({"name": validate_name(name), "score": int(score),
                    "days_completed": int(days_completed), "seed": int(seed)})
    entries = ranked(entries)
    _write(path, entries)
    return entries


def export(out_path, store_path):
    _write(out_path, load(store_path))
