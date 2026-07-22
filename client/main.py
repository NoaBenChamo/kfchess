import asyncio
import sys

from client.network_client import NetworkClient
from server.config import DEFAULT_HOST, DEFAULT_PORT


async def run_demo(host=DEFAULT_HOST, port=DEFAULT_PORT):
    uri = f"ws://{host}:{port}"
    async with NetworkClient(uri) as client:
        pong = await client.ping()
        print("ping:", pong)
        if pong.get("type") != "pong":
            raise SystemExit(1)

        auth = await client.register("DemoPlayer", "demo-pass")
        if auth.get("type") == "error":
            auth = await client.login("DemoPlayer", "demo-pass")
        print("auth:", auth)
        if auth.get("type") != "auth_ok":
            raise SystemExit(1)

        # Need a second client for matchmaking — use identify legacy for solo demo.
        identity = await client.identify("DemoPlayer")
        print("identify:", identity)
        if identity.get("type") != "identity_assigned":
            raise SystemExit(1)
        await client.receive_until("state_snapshot")

        move_response = await client.send_move("WPe2e4")
        print("move:", move_response)
        if move_response.get("type") != "move_accepted":
            raise SystemExit(1)


def main():
    host = DEFAULT_HOST
    port = DEFAULT_PORT
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        port = int(sys.argv[2])
    asyncio.run(run_demo(host=host, port=port))


if __name__ == "__main__":
    main()
