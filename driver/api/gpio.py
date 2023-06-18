import RPi.GPIO as GPIO


class Gpio:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)

    def config(self, pin, writable: bool):
        GPIO.setup(pin, GPIO.OUT if writable else GPIO.IN)

    def set_value(self, pin, value: bool):
        GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)

    def get_value(self, pin):
        return GPIO.input(pin)

