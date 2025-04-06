import logging.handlers
import os
import sys

concurrent = os.getenv('APP_LOG_CONCURRENT', '0')
if concurrent == '0':
    from logging.handlers import TimedRotatingFileHandler
else:
    from concurrent_log_handler import ConcurrentTimedRotatingFileHandler as TimedRotatingFileHandler

env = os.getenv('APP_LOG_TYPE', 'console')
level = os.getenv('APP_LOG_LEVEL', 'INFO')
if level == 'DEBUG':
    level = logging.DEBUG
elif level == 'ERROR':
    level = logging.ERROR
else:
    level = logging.INFO

modules_path = os.path.dirname(os.path.realpath(__file__))
log_dir = os.getenv('APP_LOG_DIR', os.path.join(modules_path, "logs"))
os.makedirs(log_dir, exist_ok=True)


class LoggerWriter:
    def __init__(self, level):
        self.level = level

    def write(self, message):
        if message != '\n':
            self.level(message)

    def flush(self):
        pass

    def isatty(self):
        pass


fr = "[%(asctime)s] [%(process)d] [%(levelname)s] - %(module)s.%(funcName)s (%(filename)s:%(lineno)d) - %(message)s"
logging_formatter = logging.Formatter(fr)

handlers = []
if 'file' in env:
    info_file_handler = TimedRotatingFileHandler(filename=os.path.join(log_dir, 'info.log'), when="MIDNIGHT",
                                                 interval=1,
                                                 backupCount=30)
    info_file_handler.setFormatter(logging_formatter)
    handlers.append(info_file_handler)
    error_file_handler = TimedRotatingFileHandler(filename=os.path.join(log_dir, 'error.log'), when="MIDNIGHT",
                                                  interval=1,
                                                  backupCount=30)
    error_file_handler.setFormatter(logging_formatter)
    error_file_handler.setLevel(logging.ERROR)
    handlers.append(error_file_handler)
if 'console' in env:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging_formatter)
    handlers.append(console_handler)

logging.basicConfig(level=level, handlers=handlers)

sys.stdout = LoggerWriter(logging.info)
sys.stderr = LoggerWriter(logging.error)


def get_file_logger(log_path):
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(message)s'))
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    return logger
