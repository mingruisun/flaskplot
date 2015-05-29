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
	tstart = tend - datetime.timedelta(hours=48)
	return figure_dtype_tstart_tend('pt', tstart, tend)

@app.route('/fig/<dtypes>/<tstart>/<tend>')
def figure_dtype_tstart_tend(dtypes, tstart, tend):
	log = DataLog()
	log.Open(readOnly=True)
	pkey = log.PlaceKeyGet('Living Room')
	colors = 'br'

	axes = []
	if len(dtypes) > 0:
		fig, ax1 = plt.subplots()
		axes.append(ax1)
	if len(dtypes) > 1:
		ax2 = ax1.twinx()
		axes.append(ax2)
	
	for i in range(len(axes)):
		dtype = DataType.CharToDataType(dtypes[i])
		label = DataType.Descriptions[dtype][0] + ' (' + DataType.Descriptions[dtype][1] + ')'
		times, values = log.LogQuery(pkey, dtype, tstart, tend)
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

