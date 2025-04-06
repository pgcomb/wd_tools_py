import logging
import os
import sys

logging_formats = {
    0: '%(message)s',
    1: '%(asctime)s - %(message)s',
    2: '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    3: "[%(asctime)s] [%(process)d] [%(levelname)s] - %(module)s.%(funcName)s (%(filename)s:%(lineno)d) - %(message)s",
}

global_log_type = os.getenv('APP_LOG_TYPE', 'console')
global_level = os.getenv('APP_LOG_LEVEL', 'INFO')
if global_level == 'DEBUG':
    global_level = logging.DEBUG
elif global_level == 'ERROR':
    global_level = logging.ERROR
else:
    global_level = logging.INFO
global_log_dir = os.getenv('APP_LOG_DIR', os.path.join(os.getcwd(), "logs"))


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


def set_global_logger(log_type=None, log_level=None, log_dir=None, log_format=None):
    concurrent = os.getenv('APP_LOG_CONCURRENT', '0')
    if concurrent == '0':
        from logging.handlers import TimedRotatingFileHandler
    else:
        from concurrent_log_handler import ConcurrentTimedRotatingFileHandler as TimedRotatingFileHandler
    log_type = log_type or global_log_type
    level = log_level or global_level
    if level == 'DEBUG':
        level = logging.DEBUG
    elif level == 'ERROR':
        level = logging.ERROR
    else:
        level = logging.INFO
    log_dir = log_dir or global_log_dir

    if isinstance(log_format, str):
        fr = log_format
    elif isinstance(log_format, int) and log_format in logging_formats:
        fr = logging_formats[log_format]
    else:
        fr = logging_formats[1]
    logging_formatter = logging.Formatter(fr)

    handlers = []
    if 'file' in log_type:
        os.makedirs(log_dir, exist_ok=True)
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
    if 'console' in log_type:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging_formatter)
        handlers.append(console_handler)

    logging.basicConfig(level=level, handlers=handlers)

    sys.stdout = LoggerWriter(logging.info)
    sys.stderr = LoggerWriter(logging.error)


def set_logger(name="app", log_type=None, log_level=None, log_dir=None, log_format=0, sub_dir=''):
    from logging.handlers import TimedRotatingFileHandler
    log_type = log_type or global_log_type
    level = log_level or global_level
    if level == 'DEBUG':
        level = logging.DEBUG
    elif level == 'ERROR':
        level = logging.ERROR
    else:
        level = logging.INFO
    log_dir = log_dir or global_log_dir
    if isinstance(log_format, str):
        fr = log_format
    elif isinstance(log_format, int) and log_format in logging_formats:
        fr = logging_formats[log_format]
    else:
        fr = logging_formats[1]
    logging_formatter = logging.Formatter(fr)
    handlers = []

    if 'single_file' in log_type:
        os.makedirs(os.path.join(log_dir, sub_dir), exist_ok=True)
        single_file_handler = logging.FileHandler(os.path.join(log_dir, sub_dir, f'{name}.log'))
        handlers.append(single_file_handler)
    if 'file' in log_type:
        os.makedirs(log_dir, exist_ok=True)
        info_file_handler = TimedRotatingFileHandler(filename=os.path.join(log_dir, sub_dir, f'{name}.log'),
                                                     when="MIDNIGHT",
                                                     interval=1,
                                                     backupCount=30)
        info_file_handler.setFormatter(logging_formatter)
        handlers.append(info_file_handler)
        error_file_handler = TimedRotatingFileHandler(filename=os.path.join(log_dir, sub_dir, f'{name}error.log'),
                                                      when="MIDNIGHT",
                                                      interval=1,
                                                      backupCount=30)
        error_file_handler.setFormatter(logging_formatter)
        error_file_handler.setLevel(logging.ERROR)
        handlers.append(error_file_handler)
    if 'console' in log_type:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(logging_formatter)
        handlers.append(console_handler)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    for handler in handlers:
        logger.addHandler(handler)
    return logger
