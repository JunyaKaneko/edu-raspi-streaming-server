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
from enum import Enum
from PIL import Image
from picamera import PiCamera


class CameraIsNotStarted(Exception):
    pass


class CameraState(Enum):
    SLEEP = 0
    ACTIVE = 1
    RECORD = 2


class Camera:
    def __init__(self, work_dir='/tmp', resolution=(320, 240)):
        self._camera = PiCamera()
        self._camera.resolution = resolution
        self._camera.rotation = 180
        self._is_started = False
        self._work_dir = work_dir
        self._record_dir = os.path.join(self._work_dir, 'records')
        if not os.path.exists(self._record_dir):
            os.mkdir(self._record_dir)
        self._lock_path = os.path.join(self._work_dir, 'camera_lock')
        self._sleep_flg = os.path.join(os.path.join(self._work_dir, 'camera_sleep'))
        self._record_flg = os.path.join(os.path.join(self._work_dir, 'camera_record'))
        self._delete_records_flg = \
            os.path.join(os.path.join(self._work_dir, 'camera_delete_records'))

    def __del__(self):
        self.stop_record()
        self.stop()

    def _lock(self):
        open(self._lock_path, 'w').close()

    def _unlock(self):
        if os.path.exists(self._lock_path):
            os.remove(self._lock_path)

    def start(self):
        if not self._is_started:
            self._camera.start_preview()
            self._is_started = True
            time.sleep(3)

    def stop(self):
        self._camera.stop_preview()
        self._unlock()
        self._is_started = False
        if os.path.exists(self._sleep_flg):
            os.remove(self._sleep_flg)

    def start_record(self):
        open(self._record_flg, 'w').close()

    def stop_record(self):
        if os.path.exists(self._record_flg):
            os.remove(self._record_flg)

    def _record(self, image):
        timestamp = datetime.strftime(datetime.now(), '%Y%m%d%H%I%S%f')
        image.save(os.path.join(self._record_dir, fr'{timestamp}.jpg'))

    def delete_records(self):
        if not os.path.exists(self._delete_records_flg):
            return
        for file in os.listdir(self._record_dir):
            path = os.path.join(self._record_dir, file)
            if os.path.isfile(path):
                os.remove(path)
        os.remove(self._delete_records_flg)

    @property
    def state(self):
        if os.path.exists(self._sleep_flg):
            return CameraState.SLEEP
        elif os.path.exists(self._record_flg):
            return CameraState.RECORD
        else:
            return CameraState.ACTIVE

    def capture(self):
        if not self._is_started:
            raise CameraIsNotStarted()
        image_io = io.BytesIO()
        self._camera.capture(image_io, format='jpeg')
        image_io.seek(0)
        return Image.open(image_io)

    def stream(self, fps=20):
        while True:
            if self.state in (CameraState.ACTIVE, CameraState.RECORD, ):
                image = self.capture()
                self._lock()
                image.save(os.path.join(self._work_dir, 'camera_out.jpg'))
                if self.state in (CameraState.RECORD, ):
                    self._record(image)
                self._unlock()
            self.delete_records()
            time.sleep(1 / fps)


if __name__ == '__main__':
    camera = Camera()
    camera.start()
    camera.stream(20)
