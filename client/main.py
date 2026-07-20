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

        # White pawn e2 -> e4 on the standard opening board.
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
