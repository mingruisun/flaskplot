import sqlite3
import os
import datetime
import time
import numpy as np



class Sensor:

	DHT22 = 1
	BMP180 = 2

	Descriptions = { \
		DHT22 : ('DHT22', 'Aosong(Guangzhou) Electronics Co.,Ltd' ), \
		BMP180 : ('BMP180', 'Bosch Sensortec' ), \
	}
	Parse = { \
		"DHT22" : DHT22, \
		"BMP180" : BMP180, \
	}



class Signal:

	Temperature = 1
	Pressure = 2
	RelativeHumidity = 3

	Descriptions = { \
		Temperature :		('Temperature',			'Degree Celsius'), \
		Pressure :			('Pressure',			'Pascal'), \
		RelativeHumidity :	('Relative Humidity',	'Percent RH'), \
	}
	Parse = { \
		"Temperature" : Temperature, \
		"Pressure" : Pressure, \
		"Relative Humidity" : RelativeHumidity, \
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
			self.__db.execute('CREATE TABLE places  (key INTEGER PRIMARY KEY, name TEXT)')
			self.__db.execute('CREATE TABLE sensors (key INTEGER PRIMARY KEY, name TEXT, manufacturer TEXT)')
			self.__db.execute('CREATE TABLE signals (key INTEGER PRIMARY KEY, name TEXT, unit TEXT)')
			self.__db.execute('CREATE TABLE log     (key INTEGER PRIMARY KEY, time TIMESTAMP, place INTEGER, sensor INTEGER, signal INTEGER, p25 REAL, p50 REAL, p75 REAL)')
		# Synchronize local sensors with the ones in the database
		for key, value in Sensor.Descriptions.iteritems():
			dbkey = self.SensorGet(value[0])
			if dbkey is None:
				self.SensorAdd(key, value[0], value[1])
			elif not dbkey == key:
				raise Exception('Error synchronizing local sensors with those in database: {0} has key {1} locally and {2} in database'.format(value[1], key, typeno))
		# Synchronize local signals with the ones in the database
		for key, value in Signal.Descriptions.iteritems():
			dbkey = self.SignalGet(value[0])
			if dbkey is None:
				self.SignalAdd(key, value[0], value[1])
			elif not dbkey == key:
				raise Exception('Error synchronizing local signals with those in database: {0} has key {1} locally and {2} in database'.format(value[1], key, typeno))
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
			return None
		else:
			return result[0]

	def PlaceAdd(self, name):
		key = self.PlaceGet(name)
		if key is not None:
			return key
		cursor = self.__db.cursor()
		cursor.execute('INSERT INTO places (name) VALUES (?)', (name,))
		key = cursor.lastrowid
		cursor.close()
		return key

	def SensorGet(self, name):
		cursor = self.__db.cursor()
		cursor.execute('SELECT key FROM sensors WHERE name=?', (name,))
		result = cursor.fetchone()
		cursor.close()
		if result is None:
			return None
		else:
			return result[0]
	
	def SensorAdd(self, key, name, manufacturer):
		self.__db.execute('INSERT INTO sensors (key, name, manufacturer) VALUES (?,?,?)', (key, name, manufacturer))

	def SignalGet(self, name):
		cursor = self.__db.cursor()
		cursor.execute('SELECT key FROM signals WHERE name=?', (name,))
		result = cursor.fetchone()
		cursor.close()
		if result is None:
			return None
		else:
			return result[0]
	
	def SignalAdd(self, key, name, unit):
		self.__db.execute('INSERT INTO signals (key, name, unit) VALUES (?,?,?)', (key, name, unit))

	def QueryRaw(self, place, sensor, signal, tstart, tend):
		cursor = self.__db.cursor()
		cursor.execute('SELECT time, p25, p50, p75 FROM log WHERE place=? AND sensor=? AND signal=? AND time BETWEEN ? AND ?',
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
	
	def Query(self, url, tstart, tend):
		urlSplit = url.split('.')
		if not len(urlSplit) == 3:
			raise Exception('Unable to split URL "' + url + '"')
		cursor = self.__db.cursor()
		cursor.execute('SELECT time, p25, p50, p75 FROM log WHERE place=(SELECT key FROM places WHERE name=?) AND sensor=(SELECT key FROM sensors WHERE name=?) AND signal=(select key FROM signals WHERE name=?) AND time BETWEEN ? AND ?',
			(urlSplit[0], urlSplit[1], urlSplit[2], tstart, tend))
		result = cursor.fetchall()
		cursor.close()
		times = [ row[0] for row in result ]
		values = np.array([ \
			[ row[1] for row in result ], \
			[ row[2] for row in result ], \
			[ row[3] for row in result ], \
			])
		return (times, values.T)

	def Add(self, place, sensor, signal, values):
		self.__db.execute('INSERT INTO log (time,place,sensor,signal,p25,p50,p75) VALUES (?,?,?,?,?,?,?)',
			(datetime.datetime.now(), place, sensor, signal, values[0], values[1], values[2]))


