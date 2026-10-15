from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address, ip_network
from fastapi import HTTPException
from fastapi import Request
from ..config import settings

_events: dict[str, deque[datetime]] = defaultdict(deque)


def enforce(key: str, limit: int) -> None:
    now = datetime.now(timezone.utc)
    window = now - timedelta(minutes=1)
    events = _events[key]
    while events and events[0] < window:
        events.popleft()
    if len(events) >= limit:
        raise HTTPException(429, "Please wait before trying again.")
    events.append(now)


def client_ip(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    try:
        peer_address = ip_address(peer)
    except ValueError:
        return peer
    for trusted_proxy in settings.trusted_proxy_list:
        try:
            trusted_network = ip_network(trusted_proxy, strict=False)
        except ValueError:
            continue
        if peer_address in trusted_network:
            forwarded = request.headers.get("x-forwarded-for", "")
            forwarded_ip = forwarded.split(",", 1)[0].strip()
            try:
                ip_address(forwarded_ip)
            except ValueError:
                return peer
            return forwarded_ip
    return peer
