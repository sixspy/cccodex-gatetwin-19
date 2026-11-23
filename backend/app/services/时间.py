from datetime import datetime, timedelta, timezone


def 解析(s: str) -> datetime:
    s = (s or "").replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def 加秒(s: str, n: int) -> str:
    return (解析(s) + timedelta(seconds=n)).strftime("%Y-%m-%dT%H:%M:%SZ")


def 差秒(a: str, b: str) -> int:
    return int((解析(b) - 解析(a)).total_seconds())
