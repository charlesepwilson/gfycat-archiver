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
    logger = logging.getLogger(__name__)

    def handle_exception(exc_type, exc_value, exc_traceback):
        if not issubclass(exc_type, KeyboardInterrupt):
            logger.error(
                "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
            )
        return sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_exception
