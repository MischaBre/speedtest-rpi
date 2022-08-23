##################################
# speedtest
#   by Michael Gemsa
#   22-08-16
#
# uses:
#   python                  3.7.13
#   mysql-connector-python  8.0.30
#   speedtest-cli           2.1.3
#
# description:
#   is a script to be run via cronjob for periodically testing the
#   speed of the internet connection.
#   You need a mysql database. The file mysql.cfg specifies the connection details to your database.
#   the script runs, makes a speedtest with speedtest.net, returns download speed
#   and upload speed in MBIT/s and adds the results to your database.
#   when a speedtest-error occurs it tries to add an empty element the error message including.
#
#
#
#   setup:
#   run the script with the parameter --setup to initialize the table in your database.
#   your need a sql-user with create table and insert privileges.
#
#   creates a table with:
#       id int, datum datetime, ip varchar, downspeed decimal, upspeed decimal, isp varchar, error varchar
#
##################################

### IMPORTS
import logging
import sys
import speedtest
import mysql.connector
from datetime import datetime
from logging.handlers import RotatingFileHandler

########################### GLOBALS
WORKING_DIR = ''                 # Insert your directory of /src/main/main.py here
# SPEEDTEST_GLOBALS
CONVERT_TO_MBIT = 1_000_000
MAX_SERVER = 5

# LOG_GLOBALS
LOG_LEVEL = logging.INFO
LOG_FILE = WORKING_DIR + 'speedtest.log'
LOG_MAXBYTES = 1 * 1024 * 1024
LOG_BACKUPCOUNT = 1

# define MYSQL GLOBALS load from mysql.cfg
DB_LOGIN_FILE = WORKING_DIR + 'mysql.cfg'
try:
    with open(DB_LOGIN_FILE, 'r') as DB_FILE:
        DB_FILELINES = DB_FILE.readlines()
except FileNotFoundError as err:
    print(DB_LOGIN_FILE)
    logging.error("Error: could not find mysql.cfg. Edit the mysql_example.cfg and rename it mysql.cfg")
    sys.exit(2)

DB_USER = DB_FILELINES[0].split("=")[1].rstrip('\n')
DB_PW = DB_FILELINES[1].split("=")[1].rstrip('\n')
DB_HOST = DB_FILELINES[2].split("=")[1].rstrip('\n')
DB_DB = DB_FILELINES[3].split("=")[1].rstrip('\n')
DB_TABLE = DB_FILELINES[4].split("=")[1].rstrip('\n')

# SQL QUERIES
DB_Q_INSERT = ('insert into {} '
             '(datum, ip, isp, downspeed, upspeed, error) '
             'values (%s, %s, %s, %s, %s, %s)').format(DB_TABLE)
DB_Q_SETUP = ('use {}').format(DB_DB)
DB_Q_SETUP2 = ('create table {} ('
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
    stdoutLog_f = logging.StreamHandler(stream=sys.stdout)
    logger_f.setLevel(LOG_LEVEL)
    rotLog_f.setFormatter(logFormatter)
    logger_f.addHandler(rotLog_f)
    logger_f.addHandler(stdoutLog_f)

    return logger_f, rotLog_f, stdoutLog_f


### speedTest
# speedTest makes the speedtest and returns up, downloadspeed and uploadspeed in MBIT/s
# attr:     st (speedtest.net object)
# return:   ip (String), down (float), up (float)
def speedTest() -> (str, str, float, float):
    # create speedtest Object
    logger.info('starting speedtest...')
    st = speedtest.Speedtest()
    st.get_closest_servers(MAX_SERVER)
    logger.info("speedtest created.")

    # run speedtest, store result in ip, isp, down, up
    ip = st.config.get('client').get('ip')
    isp = st.config.get('client').get('isp')
    down = st.download() / CONVERT_TO_MBIT
    up = st.upload() / CONVERT_TO_MBIT
    logger.info("speedtest done.")

    return ip, isp, down, up


### createCursor()
# creates mysql-cursor for mysql operations
# return:   mysql.connector, cursor
# raises:   mysql.connector.Error
def createCursor():
    try:
        # create mysql.connection and cursor with GLOBALS
        cn = mysql.connector.connect(user=DB_USER, password=DB_PW, host=DB_HOST, database=DB_DB, charset='ascii')
        cur = cn.cursor()
    except mysql.connector.Error as err:
        # raise mysql-error to main()
        raise err
    return cn, cur


### setupDB
# creates mysql-cursor for mysql operations. creates table as in DB_Q_SETUP defined
# return:   int     0: ran perfectly,   2: mysql-error
def setupDB() -> int:
    cnx = None
    cursor = None
    try:
        # create sql-cursor
        logger.info('creating cursor...')
        cnx, cursor = createCursor()
        logger.info('cursor created.')

        # use DB_TABLE;
        cursor.execute(DB_Q_SETUP)

        # create table DB_TABLE ( ... )
        cursor.execute(DB_Q_SETUP2)
        logger.info('tables created.')

        # commit
        cnx.commit()
        logger.info('committed.')
    except mysql.connector.Error as err:
        logger.error('Fehler! {}'.format(err))
        return 2
    finally:
        # close all possible sql connection
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()
        logger.info('db closed.')
    return 0


### insertData
# insertData takes mysql-cursor. Inserts ip, down, up in table lm_speedtest.
# Takes Strings of DB_USER, DB_PW, DB_HOST, DB_DB from Globals and ip, down, up as attr.
# Catches any mysql error.
# attr:     ip (String), down (double), up (double)
# return:   void
def insertData(ip, isp, down, up, error='') -> None:
    cnx = None
    cursor = None
    try:
        # create sql-cursor
        logger.info('creating cursor...')
        cnx, cursor = createCursor()
        logger.info("cursor created.")

        # execute INSERT...
        insertValues = (datetime.now(), ip, isp, down, up, error)
        cursor.execute(DB_Q_INSERT, insertValues)
        logger.info('data inserted.')

        # commit
        cnx.commit()
        logger.info('committed.')

    except mysql.connector.Error as err:
        # raise mysql-error to main()
        raise err

    finally:
        # close all possible sql connection
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()
        logger.info('db closed.')


### main
# return:   int     0: ran perfectly,   1: speedtest-error,     2: mysql-error
def main() -> int:
    try:
        try:
            # try speedtest
            ip, isp, down, up = speedTest()
            # try insert ip, down, up in mysql-db
            insertData(ip, isp, down, up)
            # everything went well. return 0 to main
            return 0
        except speedtest.ConfigRetrievalError as err:
            logger.error('Speedtest-Fehler! {}'.format(err))
            # insert empty data with error message
            insertData('0.0.0.0', '-', 0.0, 0.0, str(err))
            return 1
        except ValueError as err:
            logger.error('Speedtest-Fehler! {}'.format(err))
            # insert empty data with error message
            insertData('0.0.0.0', '-', 0.0, 0.0, str(err))
            return 1
    except mysql.connector.Error as db_err:
        # couldnt insert empty data
        logger.error("MySQL-Fehler! {}".format(db_err))
        return 2


### PROGRAM START
if __name__ == '__main__':
    # create global logger
    logger, rotLog, stdoutLog = createLogger()

    # check if '--setup' is in arguments
    args = sys.argv
    if args and args[len(args) - 1] == '--setup':
        sys.exit(setupDB())
    else:
        sys.exit(main())
