import serial
import logging
import time
import MySQLdb
from ConfigParser import RawConfigParser


logging.basicConfig(level=logging.DEBUG)

config = RawConfigParser()
config.read('config.ini')

db = MySQLdb.connect(
        host=config.get('database', 'host'),
        user=config.get('database', 'user'),
        passwd=config.get('database', 'password'),
        db=config.get('database', 'database'))
cur = db.cursor()

READING_INTERVAL = config.getfloat('main', 'reading_interval')

ser = serial.Serial(config.get('main', 'serial_port'), 9600, timeout=1)

time.sleep(1)

logging.debug(ser.readline())

time.sleep(10)


def parse_response(line):
    h, c = line.split(' ')

    return float(h), float(c)


if __name__ == '__main__':
    try:
        while True:
            ser.write('8')

            line = ser.readline()
            logging.debug(line.rstrip())

            # TODO: remove from arduino code
            if not line.startswith('DHT'):
                try:
                    h, c = parse_response(line)
                    f = c * (9.0/5) + 32

                    cur.execute("INSERT INTO reading (sensor_id, humidity, temperature, timestamp) VALUES (%s, %s, %s, NOW())", (1, h, c))
                    db.commit()

                    logging.debug("%s %s %s" % (h, c, f))
                except ValueError:
                    logging.warn("Invalid response: %s", line)

            time.sleep(READING_INTERVAL)

    except (KeyboardInterrupt, SystemExit):
        ser.close()
        cur.close()
        db.close()
