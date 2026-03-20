import os
import socket
import sys


def env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def check_socket(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_with_driver() -> tuple[bool, str]:
    uri = env("MONGO_URI", "mongodb://127.0.0.1:27017")
    dbname = env("MONGO_DB", "admin")

    try:
        from pymongo import MongoClient  # type: ignore

        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        ping = client.admin.command("ping")
        db = client[dbname]
        collections = db.list_collection_names()
        client.close()
        return True, f"ping={ping.get('ok')} collections={len(collections)}"
    except ModuleNotFoundError:
        return False, "pymongo not installed (socket test only)"
    except Exception as exc:
        return False, f"driver connection failed: {exc}"


def main() -> int:
    host = env("MONGO_HOST", "127.0.0.1")
    port = int(env("MONGO_PORT", "27017"))

    print(f"[MongoDB] checking socket {host}:{port} ...")
    socket_ok = check_socket(host, port)
    print(f"[MongoDB] socket: {'OK' if socket_ok else 'FAIL'}")
    if not socket_ok:
        return 1

    print("[MongoDB] checking ping/list collections ...")
    ok, message = check_with_driver()
    print(f"[MongoDB] query: {'OK' if ok else 'WARN'} - {message}")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
