"""SimpleFIN Bridge client and ingestion helpers."""

import base64
import json
import os
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()


def claim_setup_token(setup_token: str) -> str:
    """Claim a SimpleFIN setup token and return the Access URL.

    SimpleFIN setup tokens are base64-encoded claim URLs. This function
    decodes the token and POSTs to the claim URL to exchange it for a
    persistent access URL.

    This is a one-time operation. After claiming, store the returned
    access URL as SIMPLEFIN_ACCESS_URL in your .env file.

    Raises:
        httpx.HTTPStatusError: if the POST fails (e.g. already claimed).
        ValueError: if the token cannot be decoded.
    """
    try:
        claim_url = base64.b64decode(setup_token).decode("utf-8")
    except Exception:
        # Already a plain URL (not base64) — use as-is
        claim_url = setup_token

    response = httpx.post(claim_url)
    response.raise_for_status()
    return response.text.strip()


class SimpleFINClient:
    """Minimal synchronous client for the SimpleFIN Bridge API."""

    def __init__(self, access_url: str | None = None) -> None:
        """Initialise the client.

        Args:
            access_url: The SimpleFIN access URL. If *None*, the value is read
                from the ``SIMPLEFIN_ACCESS_URL`` environment variable.

        Raises:
            ValueError: if no access URL can be determined.
        """
        if access_url is None:
            access_url = os.getenv("SIMPLEFIN_ACCESS_URL")
        if not access_url:
            raise ValueError(
                "SIMPLEFIN_ACCESS_URL is not set. "
                "Run `finance sync setup <setup-token-url>` to obtain an access URL, "
                "then add it to your .env file as SIMPLEFIN_ACCESS_URL."
            )
        self.access_url = access_url.rstrip("/")

    def fetch_accounts(self, start_date: int | None = None) -> dict:
        """Fetch all accounts from the SimpleFIN /accounts endpoint.

        Args:
            start_date: Optional unix timestamp (seconds) to filter transactions.
                Only transactions on or after this date are returned.

        Returns:
            The parsed JSON response dict (contains an "accounts" list).

        Raises:
            httpx.HTTPStatusError: on non-2xx responses.
        """
        url = f"{self.access_url}/accounts"
        params: dict = {}
        if start_date is not None:
            params["start-date"] = start_date

        response = httpx.get(url, params=params, timeout=120.0)
        response.raise_for_status()
        return response.json()
