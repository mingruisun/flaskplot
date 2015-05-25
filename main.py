from datalog import DataType, DataLog
import Adafruit_BMP.BMP085 as BMP085
import time


if __name__ == '__main__':
	sensor = BMP085.BMP085()
	log = DataLog()
	log.Open()
	pkey = log.PlaceAdd('Living Room')
	while True:
		sumtemp = 0;
		for i in range(5):
			sumtemp += sensor.read_temperature()
		log.LogAdd(pkey, DataType.Temperature, sumtemp / 5.0)
		sumpress = 0;
		for i in range(5):
			sumpress += sensor.read_pressure()
		log.LogAdd(pkey, DataType.Pressure, sumpress / 5.0)
		log.Commit()
		time.sleep(100)
	log.Close()

