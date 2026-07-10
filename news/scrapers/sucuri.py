"""Bypass Sucuri CloudProxy JS challenges for automated fetches."""
import re
from urllib.parse import urlparse

import requests

B64_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
B64_LOOKUP = {char: index for index, char in enumerate(B64_ALPHABET)}


def _decode_sucuri_payload(html: str) -> str | None:
    match = re.search(r"S='([^']+)'", html)
    if not match:
        return None

    payload = match.group(1)
    buffer = 0
    bits = 0
    decoded: list[str] = []
    for index, char in enumerate(payload):
        if char not in B64_LOOKUP:
            continue
        buffer = (buffer << 6) + B64_LOOKUP[char]
        bits += 6
        while bits >= 8:
            bits -= 8
            value = (buffer >> bits) & 0xFF
            if value or index < len(payload) - 2:
                decoded.append(chr(value))
    return ''.join(decoded)


def _eval_js_string_expr(expr: str) -> str:
    """Evaluate simple JS string concatenation (literals + fromCharCode)."""
    parts = re.findall(
        r"String\.fromCharCode\((\d+)\)|'([^']*)'|\"([^\"]*)\"",
        expr,
    )
    result: list[str] = []
    for char_code, single, double in parts:
        if char_code:
            result.append(chr(int(char_code)))
        else:
            result.append(single or double)
    return ''.join(result)


def extract_sucuri_cookie(html: str) -> tuple[str, str] | None:
    """Return (cookie_name, cookie_value) from a Sucuri challenge page."""
    script = _decode_sucuri_payload(html)
    if not script:
        return None

    cookie_match = re.search(r"document\.cookie=(.+?);\s*location\.reload", script)
    if not cookie_match:
        return None

    cookie_expr = cookie_match.group(1).strip()
    var_match = re.search(r'\+\s*"="\s*\+\s*(\w+)\s*\+', cookie_expr)
    if not var_match:
        return None

    variable = var_match.group(1)
    value_match = re.search(rf'{re.escape(variable)}=([^;]+);', script)
    if not value_match:
        return None

    name_expr = re.split(r'\+\s*"="\s*\+', cookie_expr, maxsplit=1)[0]
    name = _eval_js_string_expr(name_expr)
    value = _eval_js_string_expr(value_match.group(1))
    if not name or not value:
        return None
    return name, value


def is_sucuri_challenge(html: str) -> bool:
    lowered = html.lower()
    if 'being redirected' in lowered and len(html) < 5000:
        return True
    return re.search(r"S='[A-Za-z0-9+/=]+'", html) is not None and len(html) < 5000


def fetch_with_sucuri_bypass(
    session: requests.Session,
    url: str,
    *,
    timeout: int = 20,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    """Fetch a URL, solving a Sucuri JS cookie challenge when present."""
    request_headers = headers or {}
    first = session.get(url, headers=request_headers, timeout=timeout, allow_redirects=True)
    if not is_sucuri_challenge(first.text):
        return first

    cookie = extract_sucuri_cookie(first.text)
    if not cookie:
        return first

    name, value = cookie
    hostname = urlparse(url).hostname or ''
    session.cookies.set(name, value, domain=hostname, path='/')
    return session.get(url, headers=request_headers, timeout=timeout, allow_redirects=True)
