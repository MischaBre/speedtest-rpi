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
from datetime import datetime
import speedtest
import mysql.connector

### GLOBALS
CONVERT_TO_MBIT = 1_000_000
MAX_SERVER = 5

DB_USER = 'root'
DB_PW = 'lm_mysql'
DB_HOST = 'localhost'
DB_DB = 'lm_test'
DB_TABLE = 'lm_speedtest'
DB_INSERT = ('insert into lm_speedtest ' \
            '(datum, ip, isp, downspeed, upspeed) ' \
            'values (%s, %s, %s, %s, %s)')


### FUNCTIONS

### speedTest
# speedTest makes the speedtest and returns up, downloadspeed and uploadspeed in MBIT/s
# attr:     st (speedtest.net object)
# return:   ip (String), down (double), up (double)
def speedTest():
    # create speedtest Object
    st = speedtest.Speedtest()
    st.get_closest_servers(MAX_SERVER)
    print("speedtest created")

    # run speedtest, store result in ip, down, up
    ip = st.config.get('client').get('ip')
    isp = st.config.get('client').get('isp')
    down = st.download() / CONVERT_TO_MBIT
    up = st.upload() / CONVERT_TO_MBIT
    print("speedtest done")

    return ip, isp, down, up


### insertData
# insertData creates the mysql cursor. Inserts ip, down, up in table lm_speedtest.
# Takes Strings of DB_USER, DB_PW, DB_HOST, DB_DB from Globals and ip, down, up as attr.
# Catches any mysql error.
# attr:     ip (String), down (double), up (double)
# return:   void
def insertData(ip, isp, down, up):
    cnx = None
    cursor = None
    try:
        # create sql-cursor
        cnx = mysql.connector.connect(user=DB_USER, password=DB_PW, host=DB_HOST, database=DB_DB)
        cursor = cnx.cursor()
        print("cursor created")

        # execute INSERT...
        insertValues = (datetime.now(), ip, isp, down, up)
        cursor.execute(DB_INSERT, insertValues)
        print('data inserted')

        # commit
        cnx.commit()

    except mysql.connector.Error as err:
        print("Fehler! {}".format(err))

    finally:
        # close all possible sql connection
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()
        print('db closed')


### main
def main():
    # SETUP
    ip = '0.0.0.0'
    isp = '-'
    down = up = 0.0
    errors = ''
    try:
        # try speedtest
        ip, isp, down, up = speedTest()
    except speedtest.ConfigRetrievalError as err:
        print('Fehler! {}'.format(err))
        errors = str(err)
    except ValueError as err:
        print('Fehler! {}'.format(err))
        errors = str(err)

    if not errors:
        # if no errors, insert ip, down, up in mysql-db
        insertData(ip, isp, down, up)
    else:
        # else insert row with 0s for error-indication
        insertData('0.0.0.0', '-', 0.0, 0.0)


### PROGRAM START
if __name__ == '__main__':
    main()
