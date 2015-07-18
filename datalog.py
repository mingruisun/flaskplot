import sqlite3
import os
import datetime
import time
import numpy as np



class Sensor:

	DHT22 = 1
	BMP180 = 2

	Details = { \
		DHT22 : ('DHT22', 'Aosong(Guangzhou) Electronics Co.,Ltd' ), \
		BMP180 : ('BMP180', 'Bosch Sensortec' ), \
	}



class Signal:

	Temperature = 1
	Pressure = 2
	Relative_Humidity = 3

	Details = { \
		Temperature :		('Temperature',			'Deg C'), \
		Pressure :			('Pressure',			'hPa'), \
		Relative_Humidity :	('Relative_Humidity',	'% RH'), \
	}



class DataLog:

	def __init__(self, filename='datalog.sqlite'):
		self.__filename = filename
		self.__fd = None
		self.__db = None

	def Open(self, readOnly=False):
		initDB = not os.path.exists(self.__filename)
		if readOnly:
			self.__fd = os.open(self.__filename, os.O_RDWR)
			self.__db = sqlite3.connect("/dev/fd/%d" % self.__fd, \
				detect_types=sqlite3.PARSE_DECLTYPES)
		else:
			self.__db = sqlite3.connect(self.__filename, \
				detect_types=sqlite3.PARSE_DECLTYPES)
		# Initialize database if file did not exist
		if initDB:
			self.__db.execute('CREATE TABLE places  (key INTEGER PRIMARY KEY, name TEXT, wgs84long REAL, wgs84lat REAL, heightMeters REAL)')
			self.__db.execute('CREATE TABLE sensors (key INTEGER PRIMARY KEY, name TEXT, manufacturer TEXT)')
			self.__db.execute('CREATE TABLE signals (key INTEGER PRIMARY KEY, name TEXT, unit TEXT)')
			self.__db.execute('CREATE TABLE log     (key INTEGER PRIMARY KEY, localtime TIMESTAMP, place INTEGER, sensor INTEGER, signal INTEGER, n INTEGER, p25 REAL, p50 REAL, p75 REAL)')
		# Synchronize local sensors with the ones in the database
		for key, value in Sensor.Details.iteritems():
			try:
				dbkey = self.SensorGet(value[0])
				if not dbkey == key:
					raise Exception('Error synchronizing local sensors with those in database: {0} has key {1} locally and {2} in database'.format(value[1], key, typeno))
			except:
				self.SensorAdd(key, value[0], value[1])
		# Synchronize local signals with the ones in the database
		for key, value in Signal.Details.iteritems():
			try:
				(dbkey, unit) = self.SignalGet(value[0])
				if not dbkey == key:
					raise Exception('Error synchronizing local signals with those in database: {0} has key {1} locally and {2} in database'.format(value[1], key, typeno))
			except:
				self.SignalAdd(key, value[0], value[1])
		self.Commit()

	def Close(self):
		if self.__db is not None:
			self.__db.close()
			self.__db = None
		if self.__fd is not None:
			os.close(self.__fd)
			self.__fd = None

	def Commit(self):
		self.__db.commit()
	
	def PlaceGet(self, name):
		cursor = self.__db.cursor()
		cursor.execute('SELECT key FROM places WHERE name=?', (name,))
		result = cursor.fetchone()
		cursor.close()
		if result is None:
			raise Exception('Unable to get place of name "' + name + '"')
		else:
			return result[0]

	def PlaceAdd(self, name, wgs84long, wgs84lat, heightMeters):
		key = self.PlaceGet(name)
		if key is not None:
			return key
		cursor = self.__db.cursor()
		cursor.execute('INSERT INTO places (name, wgs84long, wgs84lat, heightMeters) VALUES (?,?,?,?)', \
			(name, wgs84long, wgs84lat, heightMeters))
		key = cursor.lastrowid
		cursor.close()
		return key

	def SensorGet(self, name):
		cursor = self.__db.cursor()
		cursor.execute('SELECT key FROM sensors WHERE name=?', (name,))
		result = cursor.fetchone()
		cursor.close()
		if result is None:
			raise Exception('Unable to get sensor of name "' + name + '"')
		else:
			return result[0]
	
	def SensorAdd(self, key, name, manufacturer):
		self.__db.execute('INSERT INTO sensors (key, name, manufacturer) VALUES (?,?,?)', (key, name, manufacturer))

	def SignalGet(self, name):
		cursor = self.__db.cursor()
		cursor.execute('SELECT key, unit FROM signals WHERE name=?', (name,))
		result = cursor.fetchone()
		cursor.close()
		if result is None:
			raise Exception('Unable to get signal of name "' + name + '"')
		else:
			return (result[0], result[1])
	
	def SignalAdd(self, key, name, unit):
		self.__db.execute('INSERT INTO signals (key, name, unit) VALUES (?,?,?)', (key, name, unit))

	def QueryRaw(self, place, sensor, signal, tstart, tend):
		cursor = self.__db.cursor()
		cursor.execute('SELECT localtime, p25, p50, p75 FROM log WHERE place=? AND sensor=? AND signal=? AND localtime BETWEEN ? AND ?',
			(place, sensor, signal, tstart, tend))
		result = cursor.fetchall()
		cursor.close()
		times = [ row[0] for row in result ]
		values = np.array([ \
			[ row[1] for row in result ], \
			[ row[2] for row in result ], \
			[ row[3] for row in result ], \
			])
		return (times, values.T)

	def UrlToCursor(self, result, url, tstart=None, tend=None):
		urlSplit = url.split('.')
		if not len(urlSplit) == 3:
			raise Exception('Unable to split URL "' + url + '"')
		placekey = self.PlaceGet(urlSplit[0])
		sensorkey = self.SensorGet(urlSplit[1])
		signalkey, signalunit = self.SignalGet(urlSplit[2])
		urlSql = 'place=? and sensor=? and signal=?'
		cursor = self.__db.cursor()
		if tstart is None:
			if tend is None:
				cursor.execute('SELECT ' + result + ' FROM log WHERE ' + urlSql,
					(placekey, sensorkey, signalkey))
			else:
				cursor.execute('SELECT ' + result + ' FROM log WHERE ' + urlSql + ' AND (localtime < ?)',
					(placekey, sensorkey, signalkey, tend))
		else:
			if tend is None:
				cursor.execute('SELECT ' + result + ' FROM log WHERE ' + urlSql + ' AND (localtime > ?)',
					(placekey, sensorkey, signalkey, tstart))
			else:
				cursor.execute('SELECT ' + result + ' FROM log WHERE ' + urlSql + ' AND (localtime BETWEEN ? AND ?)',
					(placekey, sensorkey, signalkey, tstart, tend))
		return cursor

	def Query(self, url, tstart=None, tend=None):
		cursor = self.UrlToCursor('localtime, n, p25, p50, p75', url, tstart, tend)
		result = cursor.fetchall()
		#if len(result) == 0:
		#	raise Exception('Empty query for "' + url + '"')
		cursor.close()
		times = [ row[0] for row in result ]
		n = np.array([ row[1] for row in result ])
		values = np.array([ \
			[ row[2] for row in result ], \
			[ row[3] for row in result ], \
			[ row[4] for row in result ], \
			])
		return (times, n, values.T)

	def QueryAccumulates(self, url, tstart=None, tend=None):
		cursor = self.UrlToCursor('sum(n), min(p50), max(p50)', url, tstart, tend)
		result = cursor.fetchone()
		cursor.close()
		return result

	def Add(self, place, sensor, signal, values):
		n = len(values)
		p25 = np.percentile(values, 25)
		p50 = np.percentile(values, 50)
		p75 = np.percentile(values, 75)
		self.__db.execute('INSERT INTO log (localtime,place,sensor,signal,n,p25,p50,p75) VALUES (?,?,?,?,?,?,?,?)',
			(datetime.datetime.now(), place, sensor, signal, n, p25, p50, p75))


