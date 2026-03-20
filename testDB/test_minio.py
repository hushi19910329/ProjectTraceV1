import os
import socket
import sys
import urllib.error
import urllib.request


def env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def check_socket(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_get(url: str, timeout: float = 3.0) -> tuple[bool, str]:
    req = urllib.request.Request(url=url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            body = resp.read(200).decode(errors="ignore")
            return 200 <= status < 400, f"status={status} body={body}"
    except urllib.error.HTTPError as exc:
        return False, f"http error: {exc.code}"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    host = env("MINIO_HOST", "127.0.0.1")
    api_port = int(env("MINIO_PORT", "9000"))
    console_port = int(env("MINIO_CONSOLE_PORT", "9001"))
    scheme = env("MINIO_SCHEME", "http")

    print(f"[MinIO] checking socket api {host}:{api_port} ...")
    api_ok = check_socket(host, api_port)
    print(f"[MinIO] api socket: {'OK' if api_ok else 'FAIL'}")

    print(f"[MinIO] checking socket console {host}:{console_port} ...")
    console_ok = check_socket(host, console_port)
    print(f"[MinIO] console socket: {'OK' if console_ok else 'FAIL'}")

    if not api_ok:
        return 1

    live_url = f"{scheme}://{host}:{api_port}/minio/health/live"
    ready_url = f"{scheme}://{host}:{api_port}/minio/health/ready"
    print(f"[MinIO] checking health {live_url} ...")
    live_ok, live_msg = http_get(live_url)
    print(f"[MinIO] live: {'OK' if live_ok else 'FAIL'} - {live_msg}")

    print(f"[MinIO] checking health {ready_url} ...")
    ready_ok, ready_msg = http_get(ready_url)
    print(f"[MinIO] ready: {'OK' if ready_ok else 'FAIL'} - {ready_msg}")

    return 0 if (api_ok and live_ok and ready_ok) else 2


if __name__ == "__main__":
    sys.exit(main())
