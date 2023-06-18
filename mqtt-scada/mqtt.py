from dataclasses import dataclass
import enum
import threading
from typing import Callable, Any, List, Optional
from dataclass_jsonable import J
import paho.mqtt.client as mqtt
import sparkplug_b as sparkplug

import sparkplug_b_pb2

from sparkplug_b import *

from google.protobuf import json_format

DEATH_PAYLOAD = sparkplug.getNodeDeathPayload()
CONTROL_REBIRTH = 'Node Control/Rebirth'
CONTROL_REBOOT = 'Node Control/Reboot'


class MessageType(enum.Enum):
    NBIRTH = 'NBIRTH'
    NDEATH = 'NDEATH'
    DDATA = 'DDATA'
    NCMD = 'NCMD'
    DCMD = 'DCMD'


class EdgeDevice:
    def __init__(self, group, node):
        self.group = group
        self.node = node

    def get_topic(self, msg_type: MessageType, dev_id: Optional[str] = None):
        if dev_id is None:
            return f'spBv1.0/{self.group}/{msg_type.value}/{self.node}'
        else:
            return f'spBv1.0/{self.group}/{msg_type.value}/{self.node}/{dev_id}'


@dataclass
class Metric(J):
    name: str
    type: MetricDataType
    value: Any

metric_type_switcher = {
    'bool': MetricDataType.Boolean,
    'string': MetricDataType.String,
    'str': MetricDataType.String,
    'integer': MetricDataType.Int32,
    'int': MetricDataType.Int32,
    'long': MetricDataType.Int64,
    'float': MetricDataType.Float,
    'double': MetricDataType.Double
}
def get_metric_data_type(dtype: str):
    if dtype in metric_type_switcher:
        return metric_type_switcher[dtype]

    raise ValueError(f'{dtype} is not a valid metric data type')


def payload(mode: MessageType, metrics: List[Metric]) -> bytearray:
    if mode == MessageType.DDATA:
        payload = sparkplug.getDdataPayload()
    elif mode == MessageType.NBIRTH:
        payload = sparkplug.getNodeBirthPayload()

    for m in metrics:
        addMetric(payload, m.name, None, m.type, m.value)
    return bytearray(payload.SerializeToString())


class Mqtt:
    def __init__(self, url, port, device: EdgeDevice):
        self.url = url
        self.port = port
        self.client = mqtt.Client(url, port, 60)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.thd = threading.Thread(target=self.thd_main, daemon=True)

        self.device = device
        self.abort = False

        self.lock = threading.Lock()
        self.connected = False

        self.tags = {
                CONTROL_REBIRTH: (MetricDataType.Boolean, False),
                CONTROL_REBOOT: (MetricDataType.Boolean, False)
        }

    def thd_main(self):
        self.client.connect_async(self.url, self.port, 60)
        while not self.abort:
            rc = self.client.loop()
            with self.lock:
                self.connected = rc == mqtt.MQTT_ERR_SUCCESS

            if rc != mqtt.MQTT_ERR_SUCCESS:
                try:
                    time.sleep(1.0)
                    self.client.reconnect()
                except Exception as e:
                    print(f'Reconnect failed.. {e.message}')

        self.client.disconnect()

    def start(self):
        self.thd.start()

    def stop(self):
        self.abort = True
        self.thd.join()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f'Connected with result code {rc}')
        else:
            print(f'Failed to connect with result code {rc}, retrying..')
            self.connect()

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self.client.will_set(
            self.device.get_topic(MessageType.NDEATH),
            bytearray(DEATH_PAYLOAD.SerializeToString()),
            0,
            False
        )
        client.subscribe(self.device.get_topic(MessageType.NCMD))
        client.subscribe(self.device.get_topic(MessageType.DCMD))

        self.publish_birth()

    def on_message(self, client, userdata, msg):
        print(f'Message arrived: {msg.topic} -> {userdata}')
        tokens = msg.topic.split("/")

        if tokens[0] == "spBv1.0" and tokens[1] == self.device.group and (tokens[2] == "NCMD" or tokens[2] == "DCMD") and tokens[3] == self.device.node:
            inboundPayload = sparkplug_b_pb2.Payload()
            inboundPayload.ParseFromString(msg.payload)
            for metric in inboundPayload.metrics:
                if metric.name == CONTROL_REBIRTH:
                    print(f'handle {CONTROL_REBIRTH}')
                    # 'Node Control/Rebirth' is an NCMD used to tell the device/client application to resend
                    # its full NBIRTH and DBIRTH again.  MQTT Engine will send this NCMD to a device/client
                    # application if it receives an NDATA or DDATA with a metric that was not published in the
                    # original NBIRTH or DBIRTH.  This is why the application must send all known metrics in
                    # its original NBIRTH and DBIRTH messages.
                    self.publish_birth()
                elif metric.name == CONTROL_REBOOT:
                    print(f'handle {CONTROL_REBOOT}')
                    # 'Node Control/Reboot' is an NCMD used to tell a device/client application to reboot
                    # This can be used for devices that need a full application reset via a soft reboot.
                    # In this case, we fake a full reboot with a republishing of the NBIRTH and DBIRTH
                    # messages.
                    self.publish_birth()


    def _publish(self, msg_type: MessageType, dev_id:str, metrics: List[Metric]):
        with self.lock:
            if not self.connected:
                print(f'Failed to publish. MQTT not connected')
                return False
        topic = self.device.get_topic(msg_type, dev_id)
        qos = 0
        print(f'Publishing topic: {topic} (msg_type: {msg_type.value})')
        rc = self.client.publish(topic, bytearray(payload(msg_type, metrics)), qos, False)
        return rc

    def publish_birth(self):
        rc = self._publish(MessageType.NBIRTH, None, [Metric(k, v[0], v[1]) for k, v in self.tags.items()])
        print(f'Publish birth {rc}')

    def publish(self, msg: str, dev_id: str, metrics: List[Metric]):
        rebirth = False
        for m in metrics:
            if m.name not in self.tags:
                rebirth = True
            self.tags[m.name] = (m.type, m.value)

        # if rebirth:
        #     self.client.disconnect()
        #     # rc = self._publish('NBIRTH', [Metric(k, v[0], v[1]) for k, v in self.tags.items()])
        # else:
        res = self._publish(MessageType.DDATA, dev_id, metrics)
        print(f'Publish completed {msg}, rebirth:{rebirth} res:{str(res)}')
        return str(res)
