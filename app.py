#!/usr/bin/env python

import flask
import StringIO
import numpy as np
import matplotlib.pyplot as plt



app = flask.Flask(__name__)

@app.route('/fig/<start>/<end>')
def figure(start, end):
	x = np.random.rand(1, 25)
	y = np.random.rand(1, 25)
	fig = plt.figure()
	plt.plot(x, y, 'rx-')
	plt.grid()
	img = StringIO.StringIO()
	fig.savefig(img)
	img.seek(0)
	return flask.send_file(img, mimetype='image/png')

@app.route('/')
def form():
	return flask.render_template('form.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80, debug=True)

