import sqlite3
import os
import datetime
import time
import numpy as np



class DataType:

	Temperature = 1
	Pressure = 2
	RelativeHumidity = 3

	Descriptions = { \
		Temperature :		('Temperature',			'Degree Celsius'), \
		Pressure :			('Pressure',			'Pascal'), \
		RelativeHumidity :	('Relative Humidity',	'Percent RH'), \
	}

	@staticmethod
	def CharToDataType(c):
		if c == 't':
			return DataType.Temperature
		elif c == 'p':
			return DataType.Pressure
		elif c == 'h':
			return DataType.RelativeHumidity
		else:
			return None



class DataLog:

	def __init__(self, filename='datalog.sqlite'):
		self.__filename = filename
		self.__db = None
		self.__fd = None

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
			self.__db.execute('CREATE TABLE types (tkey INTEGER PRIMARY KEY, name TEXT, unit TEXT)')
			self.__db.execute('CREATE TABLE places (pkey INTEGER PRIMARY KEY, name TEXT)')
			self.__db.execute('CREATE TABLE log (lkey INTEGER PRIMARY KEY, time TIMESTAMP, place INTEGER, type INTEGER, p25 REAL, p50 REAL, p75 REAL)')
		# Synchronize data types with database
		for key, value in DataType.Descriptions.iteritems():
			tkey = self.TypeKeyGet(value[0])
			if tkey is None:
				self.TypeAdd(key, value[0], value[1])
			elif not tkey == key:
				raise Exception('Error synchronizing local data types with those in database: {0} has type number {1} locally and {2} in database'.format(value[1], key, typeno))
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
	
	def TypeKeyGet(self, name):
		cursor = self.__db.cursor()
		cursor.execute('SELECT tkey FROM types WHERE name=?', (name,))
		result = cursor.fetchone()
		cursor.close()
		if result is None:
			return None
		else:
			return result[0]
	
	def TypeAdd(self, tkey, name, unit):
		self.__db.execute('INSERT INTO types (tkey, name, unit) VALUES (?,?,?)', (tkey, name, unit))

	def PlaceKeyGet(self, name):
		cursor = self.__db.cursor()
		cursor.execute('SELECT pkey FROM places WHERE name=?', (name,))
		result = cursor.fetchone()
		cursor.close()
		if result is None:
			return None
		else:
			return result[0]

	def PlaceAdd(self, name):
		pkey = self.PlaceKeyGet(name)
		if pkey is not None:
			return pkey
		cursor = self.__db.cursor()
		cursor.execute('INSERT INTO places (name) VALUES (?)', (name,))
		pkey = cursor.lastrowid
		cursor.close()
		return pkey

	def LogAdd(self, pkey, tkey, values):
		self.__db.execute('INSERT INTO log (time,place,type,p25,p50,p75) VALUES (?,?,?,?,?,?)',
			(datetime.datetime.now(), pkey, tkey, values[0], values[1], values[2]))

	def LogQuery(self, pkey, tkey, tstart, tend):
		cursor = self.__db.cursor()
		cursor.execute('SELECT time, p25, p50, p75 FROM log WHERE place=? AND type=? AND time BETWEEN ? AND ?',
			(pkey, tkey, tstart, tend))
		result = cursor.fetchall()
		cursor.close()
		times = [ row[0] for row in result ]
		values = np.array([ \
			[ row[1] for row in result ], \
			[ row[2] for row in result ], \
			[ row[3] for row in result ], \
			])
		return (times, values.T)

