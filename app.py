#!/usr/bin/env python

import flask
import StringIO
import datetime
import numpy as np

# Import matplotlib in a way it does not use the GUI or tkinter
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
from datalog import Sensor, Signal, DataLog



app = flask.Flask(__name__)

@app.route('/')
def figure():
	tend = datetime.datetime.now()
	tstart = tend - datetime.timedelta(hours=8)
	return figure_dtype_tstart_tend('Brunnen.DHT22.Temperature,Brunnen.BMP180.Pressure,Brunnen.DHT22.Relative_Humidity', tstart, tend)

@app.route('/fig/<urls>/<tstart>/<tend>')
def figure_dtype_tstart_tend(urls, tstart, tend):
	log = DataLog()
	log.Open(readOnly=True)
	colors = 'rgb'
	urlsSplit = urls.split(',')

	ax = []
	pos = []
	if len(urlsSplit) > 0:
		host = host_subplot(111, axes_class=AA.Axes)
		ax.append(host)
		pos.append('left')
	if len(urlsSplit) > 1:
		par1 = host.twinx()
		ax.append(par1)
		pos.append('right')
	if len(urlsSplit) > 2:
		par2 = host.twinx()
		plt.subplots_adjust(right=0.75)
		offset = 60
		new_fixed_axis = par2.get_grid_helper().new_fixed_axis
		par2.axis["right"] = new_fixed_axis(loc="right", axes=par2, offset=(offset, 0))
		ax.append(par2)
		pos.append('right')
	
	for i in range(len(ax)):
		url = urlsSplit[i]
		dbkey, unit = log.SignalGet(url.split('.')[2])
		label = url + " (" + unit + ")"
		times, n, values = log.Query(url, tstart, tend)
		ax[i].plot(times, values[:,2], '-' + colors[i])
		ax[i].set_ylabel(label)
		ax[i].tick_params(axis='y', colors=colors[i], which='both')
		ax[i].axis[pos[i]].label.set_color(colors[i])
		ax[i].axis[pos[i]].major_ticklabels.set_color(colors[i])
		if i > 0:
			ax[i].axis['bottom'].toggle(all=False)

	log.Close()
	ax[0].set_xlabel('Local Time')
	ax[0].grid()
	img = StringIO.StringIO()
	plt.savefig(img, dpi=150)
	plt.close()
	img.seek(0)
	return flask.send_file(img, mimetype='image/png')

@app.route('/')
def form():
	return flask.render_template('form.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80, debug=True)

