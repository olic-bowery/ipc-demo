from dataclasses import dataclass
import json
import os
import threading
import logging

from dataclass_jsonable import J
from scale import Scale
from api.gpio import Gpio

from werkzeug.serving import make_server
from flask import Flask, render_template, Response, request

from api.logger import get_default_logger

logger = get_default_logger()


class EndpointAction(object):
    def __init__(self, action):
        self.action = action

    def __call__(self, *args):
        return Response(self.action(), status=200, headers={})


@dataclass
class GpioConfig(J):
    pin: int
    writable: bool


@dataclass
class GpioSet(J):
    pin: int
    value: bool


@dataclass
class GpioGet(J):
    pin: int


class RestServer(threading.Thread):
    def __init__(self, port, scale: Scale, gpio: Gpio):
        threading.Thread.__init__(self)
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.WARNING)

        app = Flask('HTTP server')

        # app.add_url_rule('/modbus_write', '/modbus_write', EndpointAction(self.modbus_write), methods=['POST', 'PUT'])
        app.add_url_rule('/read_weight', '/read_weight', EndpointAction(self.read_weight))
        app.add_url_rule('/tare', '/tare', EndpointAction(self.tare), methods=['POST', 'PUT'])
        app.add_url_rule('/gpio_config', '/gpio_config', EndpointAction(self.gpio_config), methods=['POST', 'PUT'])
        app.add_url_rule('/gpio_get', '/gpio_get', EndpointAction(self.gpio_get))
        app.add_url_rule('/gpio_set', '/gpio_set', EndpointAction(self.gpio_set), methods=['POST', 'PUT'])
        self.scale = scale
        self.gpio = gpio
        host = '0.0.0.0'
        self.server = make_server(host=host, port=port, app=app)
        print(f'Push REST context host={host}')
        app.app_context().push()

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()

    def gpio_set(self):
        req = json.loads(request.data)
        param: GpioSet = GpioSet.from_json(req)
        self.gpio.set_value(param.pin, param.value)

    def gpio_get(self):
        req = json.loads(request.data)
        param: GpioGet = GpioGet.from_json(req)
        dat = {"value": self.gpio.get_value(param.pin)}
        return json.dumps(dat)

    def gpio_config(self):
        req = json.loads(request.data)
        param: GpioConfig = GpioConfig.from_json(req)
        self.gpio.config(param.pin, param.writable)

    def read_weight(self):
        dat = {'weight': self.scale.read_weight()}
        return json.dumps(dat)

    def tare(self):
        self.scale.tare()
        return ''
