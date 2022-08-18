# speedtest


### speedtest

  by Michael Gemsa
  22-08-16
  
  
### uses:
  python                  3.7.13
  
  mysql-connector-python  8.0.30
  
  speedtest-cli           2.1.3
  
  
### description:

  is a script to be run via cronjob for periodically testing the
  speed of the internet connection.
  You need a mysql database. The file mysql.cfg specifies the connection details to your database.
  the script runs, makes a speedtest with speedtest.net, returns download speed
  and upload speed in MBIT/s and adds the results to your database.
  when a speedtest-error occurs it tries to add an empty element the error message including.
  
### setup:

  run the script with the parameter --setup to initialize the table in your database.
  your need a sql-user with create table and insert privileges.
  
  creates a table with:
      id int, datum datetime, ip varchar, downspeed decimal, upspeed decimal, isp varchar, error varchar
