#!/usr/bin/env python

import flask
import StringIO
import datetime
import numpy as np

# Import matplotlib in a way it does not use the GUI or tkinter
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

from datalog import DataType, DataLog



app = flask.Flask(__name__)

@app.route('/')
def figure():
	tend = datetime.datetime.now()
	tstart = tend - datetime.timedelta(hours=30)
	return figure_dtype_tstart_tend(DataType.Pressure, tstart, tend)

@app.route('/fig/<dtype>/<tstart>/<tend>')
def figure_dtype_tstart_tend(dtype, tstart, tend):
	# Extract data
	log = DataLog()
	log.Open(readOnly=True)
	pkey = log.PlaceKeyGet('Living Room')
	times, values = log.LogQuery(pkey, dtype, tstart, tend)
	print(values)
	log.Close()
	# Plot data
	fig = plt.figure()
	plt.plot(times, values[:,0]/100.0, 'b--')
	plt.plot(times, values[:,1]/100.0, 'b-')
	plt.plot(times, values[:,2]/100.0, 'b--')
	plt.axhline(y=962.0, color='r')
	plt.xlabel('Time')
	plt.ylabel('Pressure (hPa)')
	plt.grid()
	img = StringIO.StringIO()
	fig.savefig(img, dpi=150)
	img.seek(0)
	return flask.send_file(img, mimetype='image/png')

@app.route('/')
def form():
	return flask.render_template('form.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80, debug=True)

