import sqlite3
import os
import datetime
import time



class DataType:
	Temperature = 1
	Pressure = 2
	RelativeHumidity = 3

	Descriptions = { \
		Temperature :		('Temperature',			'Degree Celsius'), \
		Pressure :			('Pressure',			'Pascal'), \
		RelativeHumidity :	('Relative Humidity',	'Percent RH'), \
	}



class DataLog:

	def __init__(self, filename='datalog.sqlite'):
		self.__filename = filename
		self.__db = None

	def Open(self):
		initDB = not os.path.exists(self.__filename)
		self.__db = sqlite3.connect(self.__filename, \
			detect_types=sqlite3.PARSE_DECLTYPES)
		# Initialize database if file did not exist
		if initDB:
			self.__db.execute('CREATE TABLE types (tkey INTEGER PRIMARY KEY, name TEXT, unit TEXT)')
			self.__db.execute('CREATE TABLE places (pkey INTEGER PRIMARY KEY, name TEXT)')
			self.__db.execute('CREATE TABLE log (lkey INTEGER PRIMARY KEY, time TIMESTAMP, place INTEGER, type INTEGER, value REAL)')
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
	
	def Commit(self):
		self.__db.commit()
	
	def TypeKeyGet(self, name):
		cursor = self.__db.cursor()
		cursor.execute('select tkey from types where name=?', (name,))
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
		cursor.execute('select pkey from places where name=?', (name,))
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

	def LogAdd(self, pkey, tkey, value):
		self.__db.execute('INSERT INTO log (time,place,type,value) VALUES (?,?,?,?)', (datetime.datetime.now(),pkey,tkey,value))
		


if __name__ == '__main__':
	log = DataLog()
	log.Open()
	pkey = log.PlaceAdd('Living Room')
	for i in range(25):
		log.LogAdd(pkey, DataType.Temperature, 20.0+i)
	log.Commit()
	log.Close()

