import utime
from umqtt_simple import *

class MQTTClient(MQTTClient):

    DELAY = 2
    DEBUG = False

    def delay(self, i):
        utime.sleep(self.DELAY)

    def log(self, in_reconnect, e):
        if self.DEBUG:
            if in_reconnect:
                print("mqtt reconnect: %r" % e)
            else:
                print("mqtt: %r" % e)

    def reconnect(self):
        i = 0
        start_time = utime.ticks_ms()
        while (utime.ticks_ms() - start_time) < 10000: # reconnect in 10s
            try:
                return super().connect(False)
            except OSError as e:
                self.log(True, e)
                i += 1
                self.delay(i)

    def publish(self, topic, msg, retain=False, qos=0):
        start_time = utime.ticks_ms()
        while (utime.ticks_ms() - start_time) < 10000: # try in 10s max
            try:
                return super().publish(topic, msg, retain, qos)
            except OSError as e:
                self.log(False, e)
            self.reconnect()

    def wait_msg(self):
        start_time = utime.ticks_ms()
        while (utime.ticks_ms() - start_time) < 10000: # try in 10s max
            try:
                return super().wait_msg()
            except OSError as e:
                self.log(False, e)
            self.reconnect()
