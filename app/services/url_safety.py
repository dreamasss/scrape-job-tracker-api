from ipaddress import ip_address
from urllib.parse import urlparse

from fastapi import HTTPException

BLOCKED_HOSTNAMES = {"localhost"}


def validate_public_url(url: str) -> None:
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname

    if hostname is None:
        raise HTTPException(status_code=400, detail="Invalid URL hostname")

    if hostname.lower() in BLOCKED_HOSTNAMES:
        raise HTTPException(status_code=400, detail="Blocked private or local URL")

    try:
        ip = ip_address(hostname)
    except ValueError:
        return

    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        raise HTTPException(status_code=400, detail="Blocked private or local URL")
