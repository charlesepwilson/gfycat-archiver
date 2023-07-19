import logging
import sys

from gfycat_archiver.settings import Settings


def initialise_logger(settings_: Settings):
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
    ]
    logging.basicConfig(
        level=settings_.log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )
