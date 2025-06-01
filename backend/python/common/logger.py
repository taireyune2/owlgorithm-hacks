
import os, sys
import logging
import logging.handlers
from io import StringIO
from queue import Queue
import atexist

def setup(configs: dict) -> logging.Logger:
    """
    Setup the logger with the given configurations.
    
    Args:
        configs (dict): Configuration dictionary for logging.

    Example:
    configs = {
        "level": 20,
        "env": "dev",
        "path": "logs"
    }
    """
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(configs["level"])
    log_format = logging.Formatter(
        "%(levelname)s:%(asctime)s [%(process)d] %(filename)s:%(lineno)d %(message)s"
    )

    handlers = []

    # std out handlers
    std_handler = logging.StreamHandler()
    std_handler.setFormatter(log_format)
    handlers.append(std_handler)

    if configs.get("path", ""):
        log_stream = StringIO()
        file_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(configs['path'], configs['env'] + ".log"),
            when="midnight",
            backupCount=7,
        )
        file_handler.setFormatter(log_format)
        handlers.append(file_handler)

    ### setup queue handler
    log_queue = Queue(-1) 
    queue_handler = logging.handlers.QueueHandler(log_queue)
    queue_handler.setLevel(logger.level)
    listener = logging.handlers.QueueListener(
        log_queue,
        *handlers,
        respect_handler_level=False
    )
    listener.start()
    atexit.register(listener.stop)
    logger.addHandler(queue_handler)

    return logger

