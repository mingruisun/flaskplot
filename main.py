from datalog import DataType, DataLog
import Adafruit_BMP.BMP085 as BMP085
import time


if __name__ == '__main__':
	sensor = BMP085.BMP085()
	log = DataLog()
	log.Open()
	pkey = log.PlaceAdd('Living Room')
	while True:
		log.LogAdd(pkey, DataType.Temperature, sensor.read_temperature())
		log.LogAdd(pkey, DataType.Pressure, sensor.read_pressure())
		log.Commit()
		time.sleep(100)
	log.Close()

