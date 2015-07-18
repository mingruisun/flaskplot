from datalog import Sensor, Signal, DataLog
import Adafruit_BMP.BMP085 as BMP085
import Adafruit_DHT
import time
import numpy as np
import signal
import sys



log = DataLog()

def SignalHandler(signal, frame):
	print('\nClosing database ...\n')
	log.Close()
	sys.exit(0)


if __name__ == '__main__':
	bmp085 = BMP085.BMP085()
	dht22 = Adafruit_DHT.DHT22
	n = 50
	log.Open()
	signal.signal(signal.SIGINT, SignalHandler)
	pkey = log.PlaceAdd('Brunnen', 8.61027, 47.00130, 438.0)
	while True:
		t1 = np.zeros(n)
		p = np.zeros(n)
		h = np.zeros(n)
		t2 = np.zeros(n)
		for i in range(n):
			t1[i] = bmp085.read_temperature()
			time.sleep(0.5)
			p[i]  = bmp085.read_pressure() / 100.0	# Pa -> hPa
			time.sleep(0.5)
			h[i], t2[i] = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 4)
			time.sleep(0.5)
		log.Add(pkey, Sensor.BMP180, Signal.Temperature, t1)
		log.Add(pkey, Sensor.BMP180, Signal.Pressure, p)
		log.Add(pkey, Sensor.DHT22, Signal.Relative_Humidity, h)
		log.Add(pkey, Sensor.DHT22, Signal.Temperature, t2)
		log.Commit()

