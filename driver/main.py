
import time
from rest import RestServer
from scale import Scale
from api.gpio import Gpio


if __name__ == '__main__':
    scale = Scale()
    gpio = Gpio()
    rest = RestServer(9090, scale, gpio)

    print("Start scale")
    scale.start()
    print("Start REST")
    rest.start()

    print("Running...")
    while True:
        time.sleep(1)

    print("Bye...")
