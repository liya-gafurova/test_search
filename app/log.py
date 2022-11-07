import logging

_log_format = f"%(asctime)s - [%(levelname)s] - %(name)s - %(funcName)s - %(lineno)d - %(message)s"


def get_stream_handler():
    stream_handler = logging.FileHandler('/home/lia/PycharmProjects/bible_search/app/logged.log')
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(_log_format))
    return stream_handler


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(get_stream_handler())
    return logger