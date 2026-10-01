"""Se configuran los registros (logs) compartidos para todos los componenetes"""

import sys

from loguru import logger

from bbva_rag.config.settings import get_settings

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)


def setup_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, level=get_settings().log_level, format=LOG_FORMAT)
