

import time
from mqtt import EdgeDevice, Mqtt
from rest import RestServer


if __name__ == '__main__':
    mqtt = Mqtt('test.mosquitto.org', 1883, EdgeDevice('Demo', 'Scale'))
    print("Start mqtt")
    mqtt.start()

    rest = RestServer(9091, mqtt)
    print("Start REST")
    rest.start()

    print("Running...")
    while True:
        time.sleep(1)

    print("Bye...")
