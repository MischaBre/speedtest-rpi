import speedtest
import logging
from logging.handlers import RotatingFileHandler


def createLogger() -> (logging.Logger, logging.Handler):
    logger = logging.getLogger('speedtest_log')
    logFormatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    rotLog = logging.handlers.RotatingFileHandler(
        filename='log.test', mode='a', maxBytes=1000, backupCount=1)
    logger.setLevel(logging.INFO)
    rotLog.setFormatter(logFormatter)
    logger.addHandler(rotLog)

    return logger, rotLog

def main():
    st = speedtest.Speedtest()

if __name__ == '__main__':
    main()