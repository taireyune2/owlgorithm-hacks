import logging
import asyncio

from interviewer import console
from common import logger, configs


def main():
    logger.setup(configs.logging)
    asyncio.run(console.main_async(configs.agent))

if __name__ == "__main__":
    main()
    