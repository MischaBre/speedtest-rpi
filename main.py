import string
from datetime import date, datetime
import speedtest
import mysql.connector

#GLOBALS
CONVERT_TO_MBIT = 1_000_000
MAX_SERVER = 5
DB_USER = 'root'
DB_PW = 'lm_mysql'
DB_HOST = 'localhost'
DB_DB = 'lm_test'
DB_TABLE = 'lm_speedtest'
DB_INSERT = ('insert into lm_speedtest ' \
            '(datum, ip, downspeed, upspeed) ' \
            'values (%s, %s, %s, %s)')


###FUNCTIONS

# speedTest makes the speedtest and returns up, downloadspeed and uploadspeed in MBIT/s
# attr:     st (speedtest.net object)
# return:   ip (String), down (double), up (double)
def speedTest():
    #print(st.config)
    st = speedtest.Speedtest()
    st.get_closest_servers(MAX_SERVER)
    print("speedtest created")

    ip = st.config.get('client').get('ip')
    down = st.download() / CONVERT_TO_MBIT
    up = st.upload() / CONVERT_TO_MBIT
    print("speedtest done")

    return ip, down, up


# insertData creates the mysql cursor. Inserts ip, down, up in table lm_speedtest. Takes Strings of DB_USER and DB_DB.
# attr:     user (String), db (String)
# return:   Union[CMySQLConnection, MySQLConnection]
def insertData(ip, down, up):
    try:
        cnx = mysql.connector.connect(user=DB_USER, password=DB_PW, host=DB_HOST, database=DB_DB)
        crsr = cnx.cursor()
        print("cursor created")

        insertValues = (datetime.now(), ip, down, up)
        crsr.execute(DB_INSERT, insertValues)
        print('data inserted')

        cnx.commit()
        crsr.close()
        cnx.close()
        print('db closed')

    except mysql.connector.Error as err:
        print("Fehler! {}".format(err))
    finally:
        if crsr:
            crsr.close()
        if cnx:
            cnx.close()

### main
def main():
    errors = ''
    ip = '0.0.0.0'
    down = up = 0.0
    errors = ''
    try:
        ip, down, up = speedTest()
    except speedtest.ConfigRetrievalError as err:
        print('Fehler! {}'.format(err))
        errors = str(err)
    except ValueError as err:
        print('Fehler! {}'.format(err))
        errors = str(err)

    if not errors:
        insertData(ip, down, up)


if __name__ == '__main__':
    main()
