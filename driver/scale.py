import threading
import time

from api.hx711 import HX711


class Scale:
    def __init__(self):
        self.running = True
        self.weight_read_thd = threading.Thread(target=self.weight_read_thd_main, daemon=True)

        self.hx711 = HX711(dout=21, pd_sck=20)
        self.hx711.set_offset(66800)
        self.hx711.set_reference_unit(-20.0)
        self.weight_lock = threading.Lock()
        self.weight = 0.0

    def start(self):
        self.weight_read_thd.start()

    def stop(self):
        self.running = False
        self.weight_read_thd.join()

    def weight_read_thd_main(self):
        while self.running:
            with self.weight_lock:
                self.weight = self.hx711.get_weight()

            time.sleep(1.0)

    def read_weight(self):
        with self.weight_lock:
            return self.weight

    def tare(self):
        self.hx711.tare()