import logging
import threading

from confluent_kafka import Producer, Consumer

from .channel import MqSender, MqReceiver

logger = logging.getLogger(__name__)


class KafkaSender(MqSender):
    def __init__(self, bootstrap_servers, topic=None, security_protocol=None, sasl_mechanism=None,
                 sasl_plain_username=None, sasl_plain_password=None):
        super().__init__()
        self.topic = topic
        # logger.info(f'{(security_protocol, sasl_mechanism, sasl_plain_username, sasl_plain_password)}')
        if security_protocol and sasl_mechanism:
            self.producer = Producer({
                "bootstrap.servers": bootstrap_servers,
                'security.protocol': security_protocol,
                'sasl.mechanism': sasl_mechanism,
                'sasl.username': sasl_plain_username,
                'sasl.password': sasl_plain_password
            })
        else:
            self.producer = Producer({
                "bootstrap.servers": bootstrap_servers
            })

    def sending(self, feedback, topic=None, key=None):
        super().sending(feedback=feedback)
        topic = self.topic if topic is None else topic
        self._produce(feedback, topic, key)

    def _produce(self, message, topic=None, key=None):

        def acked(err, msg):
            if err is not None:
                logger.error('Failed to deliver message:{}'.format(err))
            else:
                logger.debug(f'message sent successfully through Topic {topic} with key {key}')

        logger.debug(f'message (type is {type(message)}) sent through Topic {topic} with key {key}: {message}')
        # Asynchronous by default ( 默认是异步发送 )
        self.producer.produce(
            topic=topic,
            key=key,
            value=message,
            callback=acked
        )
        self.producer.flush(timeout=30)


class KafkaReceiver(MqReceiver):

    def __init__(self, bootstrap_servers, topics, group_id, security_protocol=None, sasl_mechanism=None,
                 sasl_plain_username=None, sasl_plain_password=None):
        super().__init__()
        # logger.info(f'{(security_protocol, sasl_mechanism, sasl_plain_username, sasl_plain_password)}')
        if security_protocol and sasl_mechanism:
            self.consumer = Consumer({
                "bootstrap.servers": bootstrap_servers,
                'security.protocol': security_protocol,
                'sasl.mechanism': sasl_mechanism,
                'sasl.username': sasl_plain_username,
                'sasl.password': sasl_plain_password,
                'group.id': group_id,
                'max.poll.interval.ms': 3600000,
                'auto.offset.reset': 'earliest'
            })
        else:
            self.consumer = Consumer({
                "bootstrap.servers": bootstrap_servers,
                'group.id': group_id,
                'max.poll.interval.ms': 3600000,
                'auto.offset.reset': 'earliest'
            })
        self.consumer.subscribe(topics=topics)

    def _start_consuming(self):
        while True:
            try:
                msg_dict = self.consumer.poll(0.1)
                if msg_dict is None:
                    continue
                if msg_dict.error():
                    logger.error("Consumer error:{}".format(msg_dict.error()))
                    continue
                message = msg_dict.value().decode('utf-8')
                logger.info(
                    f'Kafka topic partition=({msg_dict.topic()}, {msg_dict.partition()}), offset={msg_dict.offset()},\
timestamp={msg_dict.timestamp()}, headers={msg_dict.headers()}, key={msg_dict.key()}, \
value={"--too long--" if len(message) > 500 else message}')

                super()._receive(message=message)
            except:
                logger.exception('')

    def start_receiving(self):
        super().start_receiving()
        # 新建 thread 启动
        threading.Thread(target=self._start_consuming).start()
