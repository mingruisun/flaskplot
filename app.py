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



def ParseDate(date):
	if isinstance(date, datetime.datetime):
		return date
	elif isinstance(date, basestring):
		try:
			return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
		except:
			pass
		try:
			return datetime.datetime.strptime(date, '%Y-%m-%d')
		except:
			pass
		try:
			datestr = datetime.datetime.now().strftime('%Y-%m-%d')
			return datetime.datetime.strptime(datestr + ' ' + date, '%Y-%m-%d %H:%M:%S')
		except:
			pass
		raise Exception('Unable to parse date "' + date + '"')



def DoPlot(x, y, axis, fmt):
	if not len(x) == len(y):
		raise Exception('Cannot plot, len(x)={0} but len(y)={1}'.format(len(x), len(y)))
	if len(x) == 0:
		raise Exception('No data to plot')
	# Get diff in time axis in seconds
	dt = [ (x[i+1] - x[i]).total_seconds() for i in range(len(x)-1) ]
	# Determine range [tmin..tmax] for which two samples are considered to be in the same section
	p25 = np.percentile(dt, 25)
	p50 = np.percentile(dt, 50)
	p75 = np.percentile(dt, 75)
	d = 5
	tmin = p50 + d * (p25 - p50)
	tmax = p50 + d * (p75 - p50)
	# Find sections
	indices = np.where(np.logical_or(dt < tmin, dt > tmax))[0]
	indices = np.append(indices, len(dt)-1)
	# Plot the data section-wise
	start = 0
	for end in indices:
		axis.plot(x[start:end], y[start:end], fmt)
		start = end + 1



app = flask.Flask(__name__)

@app.route('/fig/<urls>/<tstartstr>/<tendstr>')
def render_plot(urls, tstartstr, tendstr):
	tstart = ParseDate(tstartstr)
	tend = ParseDate(tendstr)
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
		try:
			url = urlsSplit[i]
			dbkey, unit = log.SignalGet(url.split('.')[2])
			label = url + " (" + unit + ")"
			times, n, values = log.Query(url, tstart, tend)
			sumn, minp50, maxp50 = log.QueryAccumulates(url)
			ax[i].set_xlim([tstart, tend])
			ax[i].set_ylim([ np.floor(minp50), np.ceil(maxp50) ])
			ax[i].set_ylabel(label)
			ax[i].tick_params(axis='y', colors=colors[i], which='both')
			ax[i].axis[pos[i]].label.set_color(colors[i])
			ax[i].axis[pos[i]].major_ticklabels.set_color(colors[i])
			DoPlot(times, values[:,2], ax[i], '-' + colors[i])
			if i > 0:
				ax[i].axis['bottom'].toggle(all=False)
		except Exception as e:
			ax[i].text(0.5, 0.25 + 0.25 * i, str(e), horizontalalignment='center', verticalalignment='center', \
				transform = ax[i].transAxes, color=colors[i])

	log.Close()
	ax[0].set_xlabel('Local Time')
	ax[0].grid()
	img = StringIO.StringIO()
	plt.savefig(img, dpi=150)
	plt.close()
	img.seek(0)
	return flask.send_file(img, mimetype='image/png')

@app.route('/fig')
def default_plot():
	tend = datetime.datetime.now()
	tstart = tend - datetime.timedelta(days=3)
	return render_plot('Brunnen.DHT22.Temperature,Brunnen.BMP180.Pressure,Brunnen.DHT22.Relative_Humidity', tstart, tend)

@app.route('/')
def form():
	return flask.render_template('form.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80, debug=False)

