# pylint: disable=too-many-return-statements
"""Health check script that makes HTTP request and validates response."""
import argparse
import sys
from typing import Tuple
from urllib.parse import urlparse

import requests

DEFAULT_URL = "http://localhost:8080/health"
HTTP_CODE_OK = 200
HTTP_CODE_DEGRADED = 503
HTTP_TIMEOUT = 10


def health_check(url: str) -> Tuple[int, str]:
    """
    Make HTTP request and validate response.

    Args:
        url: URL to check

    Returns:
        tuple: (exit_code, message) where exit_code is 0 for success, > 0 for failure
    """
    try:
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return 2, "ERR_URL_INVALID"

        http_resp = requests.get(url, timeout=HTTP_TIMEOUT)
        data = http_resp.json()
        if http_resp.status_code == HTTP_CODE_OK and all(data.values()):
            return 0, "OK"

        # Unix exit codes are limited to 1B (0-255), so we use modulo 256
        ret_code = http_resp.status_code % 256

        degraded_services = [svc for svc, status in data.items() if status is not True]
        degraded_list = "_".join(degraded_services).upper()

        return ret_code, f"ERR_DEGRADED_{http_resp.status_code}_{degraded_list}"

    except requests.exceptions.Timeout:
        return 3, "ERR_TIMEOUT"
    except requests.exceptions.ConnectionError:
        return 4, "ERR_CONNECTION"
    except requests.exceptions.JSONDecodeError:
        return 5, "ERR_INVALID_JSON"


def main() -> None:
    """Main function to parse arguments and perform health check."""
    parser = argparse.ArgumentParser(description="HTTP health check script")
    parser.add_argument("url", nargs="?", default=DEFAULT_URL, help="URL to check")
    args = parser.parse_args()
    exit_code, message = health_check(args.url)
    print(message)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
