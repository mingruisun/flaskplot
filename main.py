from datalog import Sensor, Signal, DataLog
import Adafruit_BMP.BMP085 as BMP085
import Adafruit_DHT
import time
import numpy as np
import signal
import sys



def Percentiles(v):
	return np.array([ \
		np.percentile(v, 25), \
		np.percentile(v, 50), \
		np.percentile(v, 75), \
		])
	
log = DataLog()

def SignalHandler(signal, frame):
	print('Closing database ...')
	log.Close()
	sys.exit(0)


if __name__ == '__main__':
	bmp085 = BMP085.BMP085()
	dht22 = Adafruit_DHT.DHT22
	n = 10
	log.Open()
	signal.signal(signal.SIGINT, SignalHandler)
	pkey = log.PlaceAdd('Brunnen')
	while True:
		t1 = np.zeros(n)
		p = np.zeros(n)
		h = np.zeros(n)
		t2 = np.zeros(n)
		for i in range(n):
			t1[i] = bmp085.read_temperature()
			time.sleep(3.3)
			p[i]  = bmp085.read_pressure()
			time.sleep(3.3)
			h[i], t2[i] = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 4)
			time.sleep(3.3)
		log.Add(pkey, Sensor.BMP180, Signal.Temperature, Percentiles(t1))
		log.Add(pkey, Sensor.BMP180, Signal.Pressure, Percentiles(p))
		log.Add(pkey, Sensor.DHT22, Signal.RelativeHumidity, Percentiles(h))
		log.Add(pkey, Sensor.DHT22, Signal.Temperature, Percentiles(t2))
		log.Commit()

