"""File kho v1.2: {"items":[{"id","kind","fresh"}, ...]}."""

import json
import os
import tempfile

from .errors import BadInput

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")


def _num_fresh(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= float(v) <= 100


def validate_item_list(items, kinds=KINDS):
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể")
    seen = set()
    out = []
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            raise BadInput(f"items[{i}] phải là object")
        iid, kind, fresh = it.get("id"), it.get("kind"), it.get("fresh")
        if not isinstance(iid, str) or not iid:
            raise BadInput(f"items[{i}].id phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"items: id trùng {iid}")
        seen.add(iid)
        if kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind}")
        if not _num_fresh(fresh):
            raise BadInput(f"fresh ngoài [0,100]: {fresh!r}")
        out.append({"id": iid, "kind": kind, "fresh": float(fresh)})
    return out


def validate_items(items, kinds=KINDS):
    """Tương thích: reject kho đếm (object) ở v1.2."""
    if isinstance(items, dict):
        raise BadInput("kho đếm (object) không còn hợp lệ ở contract v1.2; dùng mảng cá thể")
    return validate_item_list(items, kinds)


def read_inventory(path: str, kinds=KINDS) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> list:
    """Giỏ (mảng cá thể theo thứ tự nhặt) -> mảng items xuất kho, sắp theo id."""
    items = [{"id": h["id"], "kind": h["kind"], "fresh": h["fresh"]} for h in hold]
    return sorted(items, key=lambda x: x["id"])


def counts_from_items(items) -> dict:
    counts = {}
    for it in items:
        k = it["kind"] if isinstance(it, dict) else it
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items):
    """items: list[{id,kind,fresh}] — xuất theo id."""
    if isinstance(items, dict):
        raise BadInput("write_inventory v1.2 cần mảng cá thể")
    payload = [{"id": it["id"], "kind": it["kind"], "fresh": it["fresh"]} for it in sorted(items, key=lambda x: x["id"])]
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": payload}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
