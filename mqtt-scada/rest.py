from dataclasses import dataclass
import json
import os
import threading
import logging
from typing import Any

from dataclass_jsonable import J
from mqtt import Mqtt, Metric, get_metric_data_type

from werkzeug.serving import make_server
from flask import Flask, render_template, Response, request


class EndpointAction(object):
    def __init__(self, action):
        self.action = action

    def __call__(self, *args):
        return Response(self.action(), status=200, headers={})


@dataclass
class TagUpdate(J):
    dev_id: str
    name: str
    type: str
    value: Any


class RestServer(threading.Thread):
    def __init__(self, port, mqtt: Mqtt):
        self.mqtt: Mqtt = mqtt

        threading.Thread.__init__(self)
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.WARNING)

        app = Flask('HTTP server')

        app.add_url_rule('/update_tag', '/update_tag', EndpointAction(self.update_tag), methods=['POST', 'PUT'])
        host = '0.0.0.0'
        self.server = make_server(host=host, port=port, app=app)
        print(f'Push REST context host={host}')
        app.app_context().push()

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()

    def update_tag(self):
        print(f'update_tag: {request.data}')
        req = json.loads(request.data)
        param: TagUpdate = TagUpdate.from_json(req)
        dtype = get_metric_data_type(param.type)

        rc = self.mqtt.publish('READ/update_tag', param.dev_id, [Metric(param.name, dtype, param.value)])
        return json.dumps({ "done": rc })
