import os
import socket
from app import create_app

app = create_app()


def _can_bind(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) != 0


if __name__ == '__main__':
    preferred_port = int(os.getenv("PORT", "5000"))
    fallback_port = int(os.getenv("PORT_FALLBACK", "5001"))
    run_port = preferred_port

    if not _can_bind(preferred_port) and fallback_port != preferred_port and _can_bind(fallback_port):
        print(f"⚠ Port {preferred_port} is in use, fallback to {fallback_port}")
        run_port = fallback_port

    app.run(debug=True, host='0.0.0.0', port=run_port)


