import asyncio
import logging

from websockets.asyncio.server import serve

from server.config import DEFAULT_DB_PATH, DEFAULT_HOST, DEFAULT_PORT
from server.dal.database import Database
from server.game_server import GameServer


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def run_server(
    host=DEFAULT_HOST,
    port=DEFAULT_PORT,
    db_path=DEFAULT_DB_PATH,
):
    database = Database(db_path)
    database.connect()
    database.initialize_schema()

    game_server = GameServer(database=database)
    await game_server.start()
    try:
        async with serve(game_server.handler, host, port) as server:
            logger.info("listening on ws://%s:%s (db=%s)", host, port, db_path)
            await server.serve_forever()
    finally:
        await game_server.stop()
        database.close()


def main():
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
