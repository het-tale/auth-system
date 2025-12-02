import asyncpg
from loguru import logger
from typing import Optional
from config.config import settings


class DatabaseConnection:
    def __init__(self):
        self.connection_pool: Optional[asyncpg.Pool] = None

    async def init_connection(self):
        logger.info("initiation of DB")
        try:
            self.connection_pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL, min_size=1, max_size=10
            )
        except Exception as e:
            logger.error("Error while creating connection pool", e)
            raise

    async def get_connection(self):
        if self.connection_pool is None:
            logger.error("The connection pool is NULL")
            raise
        return self.connection_pool

    async def close_connection(self):
        logger.info("Closing Database connection")
        try:
            await self.connection_pool.close()
        except Exception as e:
            logger.error("Error occurred during close", e)


connection = DatabaseConnection()
