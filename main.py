##############################
# speedtest
#   by Michael Gemsa
#   22-08-16
#
# uses:
#   python                  3.7.13
#   mysql-connector-python  8.0.30
#   speedtest-cli           2.1.3
#


### IMPORTS
import logging
import sys

import speedtest
import mysql.connector
from datetime import datetime
from logging.handlers import RotatingFileHandler

### GLOBALS
CONVERT_TO_MBIT = 1_000_000
MAX_SERVER = 5

#
LOG_LEVEL = logging.INFO
LOG_FILE = 'speedtest.log'
LOG_MAXBYTES = 1*1024*1024
LOG_BACKUPCOUNT = 1

# define MYSQL GLOBALS from mysql.cfg
DB_LOGIN_FILE = 'mysql.cfg'
DB_FILELINES = open(DB_LOGIN_FILE, 'r').readlines()
DB_USER = DB_FILELINES[0].split("=")[1].rstrip('\n')
DB_PW = DB_FILELINES[1].split("=")[1].rstrip('\n')
DB_HOST = DB_FILELINES[2].split("=")[1].rstrip('\n')
DB_DB = DB_FILELINES[3].split("=")[1].rstrip('\n')
DB_TABLE = DB_FILELINES[4].split("=")[1].rstrip('\n')

DB_INSERT = ('insert into {} '
             '(datum, ip, isp, downspeed, upspeed, error) '
             'values (%s, %s, %s, %s, %s, %s)').format(DB_TABLE)
DB_SETUP = ('use {}').format(DB_DB)
DB_SETUP2 = ('create table {} ('
            'id int auto_increment,'
            'datum datetime not null,'
            'ip varchar(15) not null,'
            'downspeed decimal(5,2) not null,'
            'upspeed decimal(5,2) not null,'
            'isp varchar(50) not null,'
            'error varchar(100),'
            'primary key (id))').format(DB_TABLE)

### FUNCTIONS

### createLogger
def createLogger() -> (logging.Logger, logging.Handler):
    logger_f = logging.getLogger('speedtest_log')
    logFormatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    rotLog_f = logging.handlers.RotatingFileHandler(
        filename=LOG_FILE, maxBytes=LOG_MAXBYTES, backupCount=LOG_BACKUPCOUNT)
    logger_f.setLevel(LOG_LEVEL)
    rotLog_f.setFormatter(logFormatter)
    logger_f.addHandler(rotLog_f)

    return logger_f, rotLog_f


### speedTest
# speedTest makes the speedtest and returns up, downloadspeed and uploadspeed in MBIT/s
# attr:     st (speedtest.net object)
# return:   ip (String), down (float), up (float)
def speedTest() -> (str, str, float, float):
    # create speedtest Object
    st = speedtest.Speedtest()
    st.get_closest_servers(MAX_SERVER)
    logger.info("speedtest created")

    # run speedtest, store result in ip, isp, down, up
    ip = st.config.get('client').get('ip')
    isp = st.config.get('client').get('isp')
    down = st.download() / CONVERT_TO_MBIT
    up = st.upload() / CONVERT_TO_MBIT
    logger.info("speedtest done")

    return ip, isp, down, up


### createCursor()
# creates mysql-cursor for mysql operations
# return:   mysql.connector, cursor
# raises:   mysql.connector.Error
def createCursor():
    try:
        cn = mysql.connector.connect(user=DB_USER, password=DB_PW, host=DB_HOST, database=DB_DB)
        cur = cn.cursor()
    except mysql.connector.Error as err:
        raise err
    return cn, cur


### setupDB
def setupDB() -> int:
    cnx = None
    cursor = None
    try:
        # create sql-cursor
        cnx, cursor = createCursor()
        logger.info('cursor created')

        # use DB_TABLE;
        cursor.execute(DB_SETUP)

        # create table DB_TABLE ( ... )
        cursor.execute(DB_SETUP2)
        logger.info('tables created')

        cnx.commit()
        logger.info('committed')
    except mysql.connector.Error as err:
        logger.error('Fehler! {}'.format(err))
        return 2
    return 0

### insertData
# insertData takes mysql-cursor. Inserts ip, down, up in table lm_speedtest.
# Takes Strings of DB_USER, DB_PW, DB_HOST, DB_DB from Globals and ip, down, up as attr.
# Catches any mysql error.
# attr:     ip (String), down (double), up (double)
# return:   void
def insertData(ip, isp, down, up, error = '') -> None:
    cnx = None
    cursor = None
    try:
        # create sql-cursor
        cnx, cursor = createCursor()
        logger.info("cursor created")

        # execute INSERT...
        insertValues = (datetime.now(), ip, isp, down, up, error)
        cursor.execute(DB_INSERT, insertValues)
        logger.info('data inserted')

        # commit
        cnx.commit()
        logger.info('committed')

    except mysql.connector.Error as err:
        raise err

    finally:
        # close all possible sql connection
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()
        logger.info('db closed')


### main
def main() -> int:
    try:
        # try speedtest
        ip, isp, down, up = speedTest()
        # try insert ip, down, up in mysql-db
        insertData(ip, isp, down, up)
        # everything went well. return 0 to main
        return 0
    except speedtest.ConfigRetrievalError as err:
        logger.error('Speedtest-Fehler! {}'.format(err))
        try:
            insertData('0.0.0.0', '-', 0.0, 0.0, str(err))
        except mysql.connector.Error as db_err:
            logger.error("Fehler! {}".format(db_err))
            return 1
        return 1
    except ValueError as err:
        logger.error('Speedtest-Fehler! {}'.format(err))
        try:
            insertData('0.0.0.0', '-', 0.0, 0.0, str(err))
        except mysql.connector.Error as db_err:
            logger.error("Fehler! {}".format(db_err))
            return 1
        return 1
    except mysql.connector.Error as db_err:
        logger.error("Fehler! {}".format(db_err))
        return 1


### PROGRAM START
if __name__ == '__main__':
    # create global logger
    logger, rotLog = createLogger()
    args = sys.argv
    if args and args[0] == 'setup':
        sys.exit(setupDB())
    else:
        sys.exit(main())
