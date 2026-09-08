"""Service-authenticated import requests; this client never writes the database."""

import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from app.domain.finance import FinancePeriod


class SyncUnconfirmed(RuntimeError):
    pass


class SyncInProgress(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class FinanceSyncClient:
    def __init__(self, base_url: str, token: str):
        parsed = urlsplit(base_url)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username
        ):
            raise ValueError(
                "DINDIN_URL must be a private HTTP(S) URL without credentials"
            )
        if not token:
            raise ValueError("DINDIN_SYNC_TOKEN is required")
        self.url = base_url.rstrip("/") + "/api/v1/finance/sync"
        self.token = token
        self.opener = build_opener(NoRedirect())

    def synchronize(self, period: FinancePeriod) -> str:
        month = f"20{period.year}-{period.month}"
        request = Request(
            self.url,
            data=json.dumps({"month": month}).encode(),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self.opener.open(request, timeout=240) as response:
                result = json.load(response)
            if result.get("month") != month or not isinstance(
                result.get("syncedAt"), str
            ):
                raise SyncUnconfirmed("Invalid import confirmation")
            return result["syncedAt"]
        except HTTPError as error:
            if error.code in (502, 504):
                raise SyncUnconfirmed(
                    "Gateway did not confirm import completion"
                ) from None
            if error.code == 409:
                raise SyncInProgress("Import already running") from None
            raise RuntimeError(f"Dindin import failed (HTTP {error.code})") from None
        except (
            TimeoutError,
            socket.timeout,
            URLError,
            ConnectionError,
            json.JSONDecodeError,
        ) as error:
            raise SyncUnconfirmed("Import completion unconfirmed") from error
