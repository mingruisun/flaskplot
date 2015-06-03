#!/usr/bin/env python

import flask
import StringIO
import datetime
import numpy as np

# Import matplotlib in a way it does not use the GUI or tkinter
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

from datalog import Sensor, Signal, DataLog



app = flask.Flask(__name__)

@app.route('/')
def figure():
	tend = datetime.datetime.now()
	tstart = tend - datetime.timedelta(hours=48)
	return figure_dtype_tstart_tend('Brunnen.DHT22.Relative Humidity,Brunnen.BMP180.Pressure', tstart, tend)

@app.route('/fig/<urls>/<tstart>/<tend>')
def figure_dtype_tstart_tend(urls, tstart, tend):
	log = DataLog()
	log.Open(readOnly=True)
	colors = 'br'
	urlsSplit = urls.split(',')

	axes = []
	if len(urlsSplit) > 0:
		fig, ax1 = plt.subplots()
		axes.append(ax1)
	if len(urlsSplit) > 1:
		ax2 = ax1.twinx()
		axes.append(ax2)
	
	for i in range(len(axes)):
		url = urlsSplit[i]
		label = url
		times, values = log.Query(url, tstart, tend)
		axes[i].plot(times, values[:,1], '-' + colors[i])
		axes[i].set_ylabel(label, color=colors[i])
		for tl in axes[i].get_yticklabels():
			tl.set_color(colors[i])

	log.Close()
	plt.xlabel('Time')
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

