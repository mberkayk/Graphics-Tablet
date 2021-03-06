import numpy as np
import cv2 as cv
from PIL import Image
from flask import Flask, render_template, Response
import pyautogui
from flask_socketio import SocketIO, emit
import time
import evdev
from evdev import UInput, ecodes as e, AbsInfo

class ScreenCap():
	def __init__(self):
		pass
	
	def capture(self):
	  # region=(200, 200,100,100)
		img = pyautogui.screenshot(region=(200, 200,100,100)) 
		frame = np.array(img) 
		frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB) 
		time.sleep(0.010)
		ret, jpeg = cv.imencode('.jpg', frame)
		return jpeg.tobytes()


screenCap = ScreenCap()
app = Flask(__name__)
socketio = SocketIO(app)

cap = {
e.EV_KEY : [e.BTN_DIGI, e.BTN_TOOL_PEN, e.BTN_TOUCH, e.BTN_STYLUS, e.BTN_STYLUS2],
e.EV_ABS : [(e.ABS_X, AbsInfo(value=0, min=0, max=1920, fuzz=0, flat=0, resolution=1)),
            (e.ABS_Y, AbsInfo(value=0, min=0, max=1080, fuzz=0, flat=0, resolution=1)),
            (e.ABS_PRESSURE, AbsInfo(value=0, min=0, max=2047, fuzz=0, flat=0, resolution=0))],
e.EV_MSC : [e.MSC_SCAN]
}

ui = UInput(cap, name="virtual tablet")
	
	
def gen():
	while True:
		frame = screenCap.capture()
		yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
		

@app.route('/video_feed')
def video_feed():
	return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
	return render_template('index.html')

@socketio.on('message')
def handle_message(data):
  print('received message: ' + data)

@socketio.on('connect')
def test_connect():
  print('client connected')

@socketio.on('disconnect')
def test_disconnect():
  print('Client disconnected')

@socketio.on('mouseEvent')
def mouseEvent(x, y, p):
  ui.write(e.EV_ABS, e.ABS_X, int(x))
  ui.write(e.EV_ABS, e.ABS_Y, int(y))
  ui.syn()

@socketio.on('pointerDown')
def pointerDown():
  ui.write(e.EV_KEY, e.BTN_DIGI, 1)
  ui.write(e.EV_KEY, e.BTN_TOOL_PEN, 1)
  ui.write(e.EV_KEY, e.BTN_TOUCH, 1)
  ui.syn()

@socketio.on('pointerUp')
def pointerUp():
  ui.write(e.EV_KEY, e.BTN_DIGI, 0)
  ui.write(e.EV_KEY, e.BTN_TOOL_PEN, 0)
  ui.write(e.EV_KEY, e.BTN_TOUCH, 0)
  ui.syn()


# app.run(host='0.0.0.0',port='8000', debug=True)
socketio.run(app, host='0.0.0.0',port='8000', debug=False)


ui.close()
