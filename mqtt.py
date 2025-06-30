import time
import network
import ubinascii
import machine
import ujson
from umqtt_robust import MQTTClient
from utility import say

class MQTT:
    def __init__(self):
        self.client = None
        self.server = ''
        self.username = ''
        self.password = ''
        self.wifi_ssid = ''
        self.wifi_password = ''
        self.callbacks = {}
        self.last_sent = 0
        # mapping pin_number → config_id
        self.virtual_pins = {}
        self.virtual_pin_values = {}

    def __on_receive_message(self, topic: bytes, msg: bytes) -> None:
        topic_str = topic.decode('ascii')
        payload   = msg.decode('ascii')
        print(f"[MQTT] Received message → topic='{topic_str}', payload='{payload}'")
        try:
            data = ujson.loads(payload)
        except Exception as e:
            print(f"[MQTT]  JSON decode error: {e}")
            return
        if callable(self.callbacks.get(topic_str)):
            self.callbacks[topic_str](payload)

    def connect_wifi(self, ssid: str, password: str, wait_for_connected: bool = True) -> None:
        self.wifi_ssid = ssid
        self.wifi_password = password
        say('Connecting to WiFi...')
        self.station = network.WLAN(network.STA_IF)
        if self.station.active():
            self.station.active(False)
            time.sleep_ms(500)

        # Try up to 5 times
        for i in range(5):
            try:
                self.station.active(True)
                self.station.connect(ssid, password)
                break
            except OSError:
                self.station.active(False)
                time.sleep_ms(500)
                if i == 4:
                    say('Failed to connect to WiFi')
                    raise

        if wait_for_connected:
            count = 0
            while not self.station.isconnected():
                count += 1
                if count > 150:  # ~15 seconds
                    say('Failed to connect to WiFi')
                    raise
                time.sleep_ms(100)

            ip = self.station.ifconfig()[0]
            say(f'WiFi connected. IP: {ip}')

    def wifi_connected(self) -> bool:
        return self.station.isconnected()

    def connect_broker(self,
                    server: str = 'mqtt1.eoh.io',
                    port:   int = 1883,
                    username: str = '',
                    password: str = '') -> None:
        client_id = ubinascii.hexlify(machine.unique_id()).decode() \
                    + str(time.ticks_ms())
        # 1) Tạo client và connect
        self.client = MQTTClient(client_id, server, port, username, password)
        try:
            self.client.disconnect()
        except:
            pass
        self.client.connect()
        self.client.set_callback(self.__on_receive_message)
        say('Connected to MQTT broker---------------------------v1')

        # 2) Chỉ publish "online" thôi
        online_topic   = f"eoh/chip/{username}/is_online"
        online_payload = '{"ol":1}'
        # retain=True để broker lưu trạng thái online
        self.client.publish(online_topic, online_payload, retain=True, qos=1)
        say(f'Announced online on {online_topic}')


    def subscribe_config_down(self, token: str, callback=None) -> None:
        """
        Subscribe topic eoh/chip/{token}/down.
        If no callback provided, use internal handler to populate virtual_pins.
        """
        topic = f"eoh/chip/{token}/down"
        cb = callback or self._handle_config_down
        self.on_receive_message(topic, cb)

    def _handle_config_down(self, msg: str) -> None:
        """
        Default handler for config/down messages.
        Parses JSON and fills self.virtual_pins.
        """
        data = ujson.loads(msg)
        devices = data.get('configuration', {}) \
                      .get('arduino_pin', {}) \
                      .get('devices', [])
                      
        
        self.virtual_pins.clear()              
                      
        for d in devices:
            for v in d.get('virtual_pins', []):
                pin    = int(v['pin_number'])
                cfg_id = int(v['config_id'])
                self.virtual_pins[pin] = cfg_id
        print("Config received, pin→config_id:", self.virtual_pins)

    def on_receive_message(self, topic: str, callback) -> None:
        """
        Subscribe an arbitrary topic and register a callback.
        """
        full_topic = topic
        self.callbacks[full_topic] = callback
        self.client.subscribe(full_topic)
        say(f"Subscribed to {full_topic}")

    def resubscribe(self) -> None:
        """
        Re-subscribe to all topics after reconnect.
        """
        for t in self.callbacks.keys():
            self.client.subscribe(t)

    def check_message(self) -> None:
        """
        Should be called periodically.
        Checks for incoming messages and handles reconnection logic.
        """
        print("[MQTT]   check_message()")
        if not self.client:
            return
        if not self.wifi_connected():
            say('WiFi disconnected. Reconnecting...')
            self.connect_wifi(self.wifi_ssid, self.wifi_password)
            self.client.connect()
            self.resubscribe()
        self.client.check_msg()

    def publish(self, topic: str, message: str) -> None:
        """
        Publish a string message to a topic, throttled to 1s between sends.
        """
        if not self.client:
            return
        now = time.ticks_ms()
        if now - self.last_sent < 100:
            time.sleep_ms(100 - (now - self.last_sent))
        full_topic = topic
        self.client.publish(full_topic, message)
        self.last_sent = time.ticks_ms()

    def virtual_write(self, pin: int, value: Union[int, float, str], username: str = '') -> None:
        """
        Publish a value to a virtual pin. Payload is JSON {"value": value}.
        """
        say(f"virtual_write(pin={pin}, value={value}, username={username})")
        if pin not in self.virtual_pins:
            say(f"  Pin {pin} chưa được đăng ký")
            return

        cfg_id = self.virtual_pins[pin]
        token = username or getattr(self, 'token', '')
        topic = f"eoh/chip/{username}/config/{cfg_id}/value"
        # Build JSON payload using ujson
        # Ensure payload uses integer 'v' key, as required by server
        payload = f'{{"v": {value}}}'

        say(f" virtual publish → topic={topic}, payload={payload}")
        # Publish with retain and QoS=1 to ensure delivery
        self.client.publish(topic, str(payload), retain=True, qos=1)
        
    def subscribe_virtual_pin(self, pin: int, token: str, callback=None) -> None:
        """
        Subscribe to topic eoh/chip/{token}/virtual_pin/{pin_number}
        to receive data from virtual pin.
        """
        topic = f"eoh/chip/{token}/virtual_pin/{pin}"
        
        if callback is None:
            # Tạo callback wrapper để lưu pin number
            def pin_callback(msg):
                self._handle_virtual_pin_data(msg, pin)
            cb = pin_callback
        else:
            cb = callback
            
        self.on_receive_message(topic, cb)
        say(f"Subscribed to virtual pin V{pin}")

    def _handle_virtual_pin_data(self, msg: str, pin: int = None) -> None:
        """
        Default handler for virtual pin data messages.
        Parses JSON and stores the received value.
        Expected format: {"value": 5, "trigger_id": 2509389}
        """
        try:
            data = ujson.loads(msg)
            value = data.get('value', 'Unknown')
            trigger_id = data.get('trigger_id', None)
            print(f"[Virtual Pin V{pin}] Received value: {value}, trigger_id: {trigger_id}")
            
            # Lưu giá trị vào dict nếu có pin number
            if pin is not None:
                self.virtual_pin_values[pin] = {
                    "value": value, 
                    "trigger_id": trigger_id,
                    "timestamp": time.ticks_ms()
                }
        except Exception as e:
            print(f"[Virtual Pin] JSON decode error: {e}")
            print(f"[Virtual Pin] Raw message: {msg}")

    def get_virtual_pin_value(self, pin: int) -> dict:
        """
        Get the latest value received from a virtual pin.
        Returns dict with 'value', 'trigger_id', 'timestamp' or None if no data.
        """
        return self.virtual_pin_values.get(pin, None)
    
    def get_virtual_pin_simple_value(self, pin: int) -> any:
        """
        Get only the value (not trigger_id/timestamp) from a virtual pin.
        Returns the value or None if no data.
        """
        data = self.virtual_pin_values.get(pin, None)
        return data.get('value', None) if data else None    
    
    def subscribe_and_get(self, pin: int, token: str) -> any:
        self.subscribe_virtual_pin(pin, token)
        return self.get_virtual_pin_simple_value(pin)

mqtt = MQTT()



