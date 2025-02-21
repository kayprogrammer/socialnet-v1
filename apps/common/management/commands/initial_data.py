from django.core.management.base import BaseCommand
from .data_script import CreateData
import logging, asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init() -> None:
    create_data = CreateData()
    await create_data.initialize()


class Command(BaseCommand):
    def handle(self, **options) -> None:
        logger.info("Creating initial data")
        asyncio.run(init())
        logger.info("Initial data created")
