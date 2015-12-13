#!/usr/bin/env python

import flask
import StringIO
import datetime
from dateutil import tz
import numpy as np
import ephem

# Import matplotlib in a way it does not use the GUI or tkinter
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
from datalog import Sensor, Signal, DataLog



# Convert local time or vector of local times to UTC time
def LocalTimeToUtc(localtime):
	if isinstance(localtime, datetime.datetime):
		return localtime.replace(tzinfo=tz.tzlocal()).astimezone(tz.tzutc())
	elif isinstance(localtime, list):
		return [ t.replace(tzinfo=tz.tzlocal()).astimezone(tz.tzutc()) for t in localtime ]
	else:
		raise Exception('Local time ' + str(localtime) + ' has unknown type ' + str(type(localtime)))



# Convert UTC time or vector of local times to local time
def UtcToLocalTime(utctime):
	if isinstance(utctime, datetime.datetime):
		return utctime.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
	elif isinstance(utctime, list):
		return [ t.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()) for t in utctime ]
	else:
		raise Exception('UTC time ' + str(utctime) + ' has unknown type ' + str(type(utctime)))



# Take local date in any form and return UTC time
def ParseDate(localdate):
	if isinstance(localdate, datetime.datetime):
		return LocalTimeToUtc(localdate)
	elif isinstance(localdate, basestring):
		if localdate == 'now':
			return datetime.datetime.utcnow()
		try:
			return LocalTimeToUtc(datetime.datetime.strptime(localdate, '%Y-%m-%d %H:%M:%S'))
		except:
			pass
		try:
			return LocalTimeToUtc(datetime.datetime.strptime(localdate, '%Y-%m-%d'))
		except:
			pass
		try:
			datestr = datetime.datetime.utcnow().strftime('%Y-%m-%d')
			return LocalTimeToUtc(datetime.datetime.strptime(datestr + ' ' + localdate, '%Y-%m-%d %H:%M:%S'))
		except:
			pass
		raise Exception('Unable to parse date "' + localdate + '"')
	else:
		raise Exception('Date ' + str(localdate) + ' has unknown type ' + str(type(localdate)))



def GetSunEvents(wgs84long, wgs84lat, utcdate):
	o = ephem.Observer()
	o.long = wgs84long
	o.lat = wgs84lat
	sun = ephem.Sun()
	sunrise = o.previous_rising(sun, start=utcdate)
	noon = o.next_transit(sun, start=sunrise)
	sunset = o.next_setting(sun, start=noon)
	return sunrise, sunset



def GetSunEventsInDateRange(wgs84long, wgs84lat, tstart, tend):
	numdays = int(np.ceil((tend - tstart).total_seconds() / (24.0 * 60.0 * 60.0))) + 1
	days = [ (tstart + datetime.timedelta(days=d)).replace(hour=12, minute=0, second=0, microsecond=0) for d in range(numdays) ]
	events = []
	for d in days:
		events.append(GetSunEvents(wgs84long, wgs84lat, d))
	return events



def PlotDayNight(axis, tstart, tend, wgs84long, wgs84lat):
	events = GetSunEventsInDateRange(str(wgs84long), str(wgs84lat), tstart, tend)
	axis.axvspan(tstart, tend, facecolor='0.5', alpha=0.5)
	for e in events:
		t0 = UtcToLocalTime(e[0].datetime())
		t1 = UtcToLocalTime(e[1].datetime())
		axis.axvspan(t0, t1, facecolor='1.0')



def DoPlot(x, y, axis, fmt):
	if not len(x) == len(y):
		raise Exception('Cannot plot, len(x)={0} but len(y)={1}'.format(len(x), len(y)))
	if len(x) == 0:
		raise Exception('No data to plot')
	x = UtcToLocalTime(x)
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
			ax[i].set_xlim(UtcToLocalTime([tstart, tend]))
			ax[i].set_ylim([ np.floor(minp50), np.ceil(maxp50) ])
			ax[i].set_ylabel(label)
			ax[i].tick_params(axis='y', colors=colors[i], which='both')
			ax[i].axis[pos[i]].label.set_color(colors[i])
			ax[i].axis[pos[i]].major_ticklabels.set_color(colors[i])
			DoPlot(times, values[:,2], ax[i], '-' + colors[i])
			if i > 0:
				ax[i].axis['bottom'].toggle(all=False)
		except Exception as e:
			ax[i].text(0.5, (1 + i) / (len(ax) + 1.0), str(e), horizontalalignment='center', verticalalignment='center', \
				transform = ax[i].transAxes, color=colors[i])

	placeName = url.split('.')[0]
	wgs84long, wgs84lat, heightMeters = log.PlaceDetailsGet(placeName)
	PlotDayNight(ax[0], tstart, tend, wgs84long, wgs84lat)
	ax[0].axis["bottom"].major_ticklabels.set_rotation(30)
	ax[0].axis["bottom"].major_ticklabels.set_ha("right")
	ax[0].grid()

	log.Close()
	img = StringIO.StringIO()
	plt.savefig(img, dpi=150)
	plt.close()
	img.seek(0)
	return flask.send_file(img, mimetype='image/png')

@app.route('/fig')
def default_plot():
	tend = datetime.datetime.utcnow()
	tstart = tend - datetime.timedelta(days=3)
	return render_plot('Brunnen.DHT22.Temperature,Brunnen.BMP180.Pressure,Brunnen.DHT22.Relative_Humidity', tstart, tend)

@app.route('/')
def form():
	return flask.render_template('form.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80, debug=False)

