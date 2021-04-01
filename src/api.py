# Copyright 2021 Morning Project Samurai, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR
# A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import os
import io
import time
from datetime import datetime
from zipfile import ZipFile
from flask import Flask, Response, jsonify, send_file


WORKDIR = '/tmp'
CAMERA_RECORD_DIR = os.path.join(WORKDIR, 'records')
CAMERA_RECORD_ZIP = os.path.join(WORKDIR, 'records.zip')
CAMERA_OUT = os.path.join(WORKDIR, 'camera_out.jpg')
CAMERA_LOCK = os.path.join(WORKDIR, 'camera_lock')
CAMERA_SLEEP = os.path.join(WORKDIR, 'camera_sleep')
CAMERA_RECORD = os.path.join(WORKDIR, 'camera_record')
CAMERA_DELETE_RECORDS = os.path.join(WORKDIR, 'camera_delete_records')
CAM_OUT = os.path.join(WORKDIR, 'cam_out.jpg')
CAM_LOCK = os.path.join(WORKDIR, 'cam_lock')

app = Flask(__name__)


def capture():
    while True:
        if os.path.exists(CAMERA_LOCK) or os.path.exists(CAMERA_SLEEP):
            continue
        with open(CAMERA_OUT, 'rb') as f:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + f.read() + b'\r\n\r\n')
        time.sleep(0.5)


def get_cam():
    while True:
        if os.path.exists(CAM_LOCK):
            continue
        with open(CAM_OUT, 'rb') as f:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + f.read() + b'\r\n\r\n')
        time.sleep(0.5)


@app.route('/cam/stream')
def stream_cam():
    return Response(get_cam(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video/stream')
def stream_video():
    return Response(capture(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video/activate')
def start_video():
    if os.path.exists(CAMERA_SLEEP):
        os.remove(CAMERA_SLEEP)
    return jsonify({'message': 'Camera is activated.'})


@app.route('/video/deactivate')
def stop_video():
    open(CAMERA_SLEEP, 'w').close()
    return jsonify({'message': 'Camera is deactivated.'})


@app.route('/video/records/start')
def start_video_record():
    open(CAMERA_RECORD, 'w').close()
    return jsonify({'message': 'Start recording.'})


@app.route('/video/records/stop')
def stop_video_record():
    if os.path.exists(CAMERA_RECORD):
        os.remove(CAMERA_RECORD)
    return jsonify({'message': 'Stop recording.'})


@app.route('/video/records/delete')
def delete_video_records():
    open(CAMERA_DELETE_RECORDS, 'w').close()
    return jsonify({'message': 'Records are deleted.'})


@app.route('/video/records/download')
def download_video_records():
    if os.path.exists(CAMERA_RECORD_ZIP):
        os.remove(CAMERA_RECORD_ZIP)
    records = io.BytesIO()
    with ZipFile(records, 'w') as f:
        for file in os.listdir(CAMERA_RECORD_DIR):
            path = os.path.join(CAMERA_RECORD_DIR, file)
            f.write(path, f'records/{file}')
    records.seek(0)
    timestamp = datetime.strftime(datetime.now(), '%Y%m%d%H%I%S%f')
    response = send_file(records,
                         attachment_filename=f'camera_records_{timestamp}.zip',
                         as_attachment=True)
    response.headers['Last-Modified'] = datetime.now()
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, ' \
                                        'post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
