"""
Server-side barcode scanning using OpenCV + pyzbar.
Runs in a background thread and emits SocketIO events on each scan.
"""
import threading
import cv2
from pyzbar import pyzbar
from config import CAMERA_INDEX


class BarcodeScanner:
    def __init__(self, socketio, on_scan_callback):
        self.socketio = socketio
        self.on_scan = on_scan_callback
        self._thread = None
        self._running = False
        self._seen = set()
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self._seen.clear()
        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()

    def stop(self):
        with self._lock:
            self._running = False

    def reset(self):
        with self._lock:
            self._seen.clear()

    def _scan_loop(self):
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            self.socketio.emit("scanner_error", {"message": "Cannot open camera"})
            self._running = False
            return

        self.socketio.emit("scanner_status", {"status": "started"})

        while True:
            with self._lock:
                if not self._running:
                    break

            ret, frame = cap.read()
            if not ret:
                continue

            barcodes = pyzbar.decode(frame)
            for bc in barcodes:
                code = bc.data.decode("utf-8").strip()
                if not code:
                    continue
                with self._lock:
                    if code in self._seen:
                        self.socketio.emit("duplicate_scan", {"barcode": code})
                        continue
                    self._seen.add(code)

                result = self.on_scan(code)
                self.socketio.emit("scan_result", result)

        cap.release()
        self.socketio.emit("scanner_status", {"status": "stopped"})