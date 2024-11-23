import logging
import os

def setup_logger(name, log_file, level=logging.INFO):
    """
    Set up a logger with the specified name, log file, and logging level.
    """
    # Ensure the logs directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

# Loggers for different modules
api_logger = setup_logger("api_logger", "logs/api.log")
redis_logger = setup_logger("redis_logger", "logs/redis.log")
db_logger = setup_logger("db_logger", "logs/db.log")
