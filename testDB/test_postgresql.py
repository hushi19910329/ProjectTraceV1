import os
import socket
import sys


def env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def safe_text(value: str) -> str:
    return value.encode("ascii", errors="replace").decode("ascii")


def check_socket(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_with_driver() -> tuple[bool, str]:
    host = env("PG_HOST", "127.0.0.1")
    port = int(env("PG_PORT", "5432"))
    user = env("PG_USER", "postgres")
    password = env("PG_PASSWORD", "Admin2023!")
    dbname = env("PG_DB", "postgres")
    sslmode = env("PG_SSLMODE", "disable")

    dsn = (
        f"host={host} port={port} user={user} password={password} "
        f"dbname={dbname} sslmode={sslmode}"
    )

    # Try psycopg (v3) first, then psycopg2.
    try:
        import psycopg  # type: ignore

        with psycopg.connect(dsn, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("select current_database(), version();")
                row = cur.fetchone()
                return True, f"db={row[0]} version={safe_text(str(row[1]))}"
    except ModuleNotFoundError:
        pass
    except Exception as exc:
        return False, f"driver connection failed: {exc}"

    try:
        import psycopg2  # type: ignore

        conn = psycopg2.connect(dsn, connect_timeout=3)
        cur = conn.cursor()
        cur.execute("select current_database(), version();")
        row = cur.fetchone()
        cur.close()
        conn.close()
        return True, f"db={row[0]} version={safe_text(str(row[1]))}"
    except ModuleNotFoundError:
        return False, "psycopg/psycopg2 not installed (socket test only)"
    except Exception as exc:
        return False, f"driver connection failed: {exc}"


def main() -> int:
    host = env("PG_HOST", "127.0.0.1")
    port = int(env("PG_PORT", "5432"))

    print(f"[PG] checking socket {host}:{port} ...")
    socket_ok = check_socket(host, port)
    print(f"[PG] socket: {'OK' if socket_ok else 'FAIL'}")
    if not socket_ok:
        return 1

    print("[PG] checking database login/query ...")
    ok, message = check_with_driver()
    print(f"[PG] query: {'OK' if ok else 'WARN'} - {safe_text(message)}")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
