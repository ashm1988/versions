import mysql.connector

config = {
  'user': 'root',
  'password': '',
  'host': '127.0.0.1',
  'database': 'versions',
}

tables = {}

tables['current'] = (
    "CREATE TABLE IF NOT EXISTS `current` ("
    "`server` VARCHAR(35) NOT NULL,"
    "`instance` VARCHAR(35) NOT NULL,"
    "`product` VARCHAR(35) NOT NULL,"
    "`core` VARCHAR(35) NOT NULL,"
    "`otl` VARCHAR(35) NOT NULL,"
    "`licence` VARCHAR(35) NOT NULL,"
    "`adapter` VARCHAR(35) NOT NULL,"
    "`frapi` VARCHAR(35) NOT NULL)"
)

tables['archive'] = (
    "CREATE TABLE IF NOT EXISTS `archive` ("
    "`date` DATE NOT NULL,"
    "`server` VARCHAR(35) NOT NULL,"
    "`instance` VARCHAR(35) NOT NULL,"
    "`product` VARCHAR(35) NOT NULL,"
    "`core` VARCHAR(35) NOT NULL,"
    "`otl` VARCHAR(35) NOT NULL,"
    "`licence` VARCHAR(35) NOT NULL,"
    "`adapter` VARCHAR(35) NOT NULL,"
    "`frapi` VARCHAR(35) NOT NULL)"
)


cnx = mysql.connector.connect(**config)
cur = cnx.cursor()

for table in tables:
    cur.execute(tables[table])


cnx.close