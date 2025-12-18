import logging
from pathlib import Path

def setup_logger(name: str) -> logging.Logger:
    Path('storage/logs').mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(f'storage/logs/{name}.log')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger
