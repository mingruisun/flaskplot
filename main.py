from datalog import DataType, DataLog
import Adafruit_BMP.BMP085 as BMP085
import time
import numpy as np



def DoSample(f, numSamples):
	values = np.zeros(numSamples)
	for i in range(numSamples):
		values[i] = f()
	return np.array([ \
		np.percentile(values, 25), \
		np.percentile(values, 50), \
		np.percentile(values, 75), \
		])



if __name__ == '__main__':
	sensor = BMP085.BMP085()
	log = DataLog()
	log.Open()
	pkey = log.PlaceAdd('Living Room')
	while True:
		t = DoSample(sensor.read_temperature, 10)
		p = DoSample(sensor.read_pressure, 10)
		log.LogAdd(pkey, DataType.Temperature, t)
		log.LogAdd(pkey, DataType.Pressure, p)
		log.Commit()
		time.sleep(100)
	log.Close()

