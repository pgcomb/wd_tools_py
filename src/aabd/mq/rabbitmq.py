import logging
import threading
import time

from .channel import MqReceiver, MqSender
import pika
from pika.exchange_type import ExchangeType

logger = logging.getLogger('rabbitmq')


def get_connection_from_config(host, port, username, password, virtual_host, heartbeat=None):
    # 连接服务器
    credentials = pika.PlainCredentials(username=username, password=password) if username and password else None
    connection = pika.BlockingConnection(
        # heartbeat=0会导致重启的时候老的consumer channel不会被server端主动检测到超时而断开
        (
            pika.ConnectionParameters(host=host, port=port, credentials=credentials, virtual_host=virtual_host,
                                      heartbeat=heartbeat)
            if heartbeat is not None else
            pika.ConnectionParameters(host=host, port=port, credentials=credentials, virtual_host=virtual_host)
        )
        if credentials else
        (
            pika.ConnectionParameters(host=host, port=port, virtual_host=virtual_host, heartbeat=heartbeat)
            if heartbeat is not None else
            pika.ConnectionParameters(host=host, port=port, virtual_host=virtual_host)
        )
    )
    return connection


class RabbitmqReceiver(MqReceiver):

    def __init__(self, host="127.0.0.1", port=5672, username='admin', password='admin', virtual_host='/',
                 heartbeat=None,
                 consumer_exchange=None, consumer_routing_key=None, consumer_queue=None,
                 exchange_type=ExchangeType.topic, configuration=None):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.virtual_host = virtual_host
        self.heartbeat = heartbeat
        if configuration is None:
            configuration = {}
        self.consumer_queue = consumer_queue
        self.consumer_routing_key = consumer_routing_key
        self.consumer_exchange = consumer_exchange
        self.exchange_type = exchange_type
        self.extra_configuration = configuration.get('extra') if configuration.get('extra') else {}
        self._link()

    def _link(self):
        consumer_connection: pika.BlockingConnection = get_connection_from_config(self.host, self.port, self.username,
                                                                                  self.password,
                                                                                  self.virtual_host, self.heartbeat)
        logger.info(f'consumer_connection_dict = {consumer_connection.__dict__}')

        self.consumer_message_channel: pika.adapters.blocking_connection.BlockingChannel = consumer_connection.channel()
        logger.info(f'consumer_channel_dict = {self.consumer_message_channel.__dict__}')
        logger.info(f'consumer_tag = {self.consumer_message_channel.consumer_tags}')

        if self.consumer_exchange is not None:
            self.consumer_message_channel.exchange_declare(exchange=self.consumer_exchange,
                                                           exchange_type=self.exchange_type,
                                                           durable=True)
        if self.consumer_queue is not None and self.consumer_routing_key is not None:
            self.consumer_message_channel.queue_declare(queue=self.consumer_queue, durable=True)
            self.consumer_message_channel.queue_bind(queue=self.consumer_queue, exchange=self.consumer_exchange,
                                                     routing_key=self.consumer_routing_key)

    def __on_message_callback(self, channel, method, properties, message):
        logger.debug(f'message (type is {type(message)}) received through Queue {self.consumer_queue}: {message}')

        thread = threading.Thread(target=super()._receive, args=[message],
                                  kwargs={'method': method, "properties": properties})
        thread.start()

        while thread.is_alive():  # Loop while the thread is processing
            logger.debug(f' loop {self.consumer_queue} process_data_events while the thread is processing message')
            channel._connection.sleep(1.0)
        logger.debug(
            f'Back from thread for Queue {self.consumer_queue}, and channel has {channel.get_waiting_message_count()} messages more')
        if self.auto_ack is False:
            logger.info(f'basic_ack: {method.delivery_tag}')
            channel.basic_ack(delivery_tag=method.delivery_tag)

    def start_receiving(self):
        super().start_receiving()
        # 新建 thread 启动
        threading.Thread(target=self.reconnected_logic).start()

    def reconnected_logic(self):
        thread = threading.Thread(target=self._start_consuming)
        thread.start()
        while True:
            a = self.consumer_message_channel.is_open
            b = self.consumer_message_channel.is_closed
            c = self.consumer_message_channel.connection.is_open
            d = self.consumer_message_channel.connection.is_closed
            if a == b or c == d or a != c:
                logger.info(f'WEIRED! {self.consumer_queue} consumer channel status: {a} {b} {c} {d}')
            if not b:
                if not thread.is_alive():
                    logger.info(f'AGAIN! {self.consumer_queue} consumer thread is dead')
                    thread = threading.Thread(target=self._start_consuming)
                    thread.start()
            else:
                logger.info(f'AGAIN! {self.consumer_queue} consumer channel is closed')
                if thread.is_alive():
                    logger.info(
                        f'{self.consumer_queue} consumer channel is closed, but blocked in consuming thread??? do stopping')
                    self.consumer_message_channel.stop_consuming()
                self._link()
                thread = threading.Thread(target=self._start_consuming)
                thread.start()
            time.sleep(2)

    def _start_consuming(self):
        # https://blog.csdn.net/m0_46825740/article/details/120220791
        try:
            self.consumer_message_channel.basic_qos(prefetch_count=1)
            self.auto_ack = self.extra_configuration.get('autoAck')
            if self.auto_ack is False:
                self.consumer_message_channel.basic_consume(queue=self.consumer_queue,
                                                            on_message_callback=self.__on_message_callback)
            else:
                self.auto_ack = True
                self.consumer_message_channel.basic_consume(queue=self.consumer_queue,
                                                            on_message_callback=self.__on_message_callback,
                                                            auto_ack=True)
            self.consumer_message_channel.start_consuming()
        except:
            logger.error(f'{self.consumer_queue} channel consuming error', exc_info=True, stack_info=True)
        finally:
            logger.info(f'{self.consumer_queue} consuming seems to have been stopped')


class RabbitmqSender(MqSender):

    def __init__(self, host="127.0.0.1", port=5672, username='admin', password='admin', virtual_host='/',
                 heartbeat=None, producer_exchange=None, producer_routing_key=None, exchange_type=ExchangeType.topic):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.virtual_host = virtual_host
        self.heartbeat = heartbeat
        self.producer_exchange = producer_exchange
        self.exchange_type = exchange_type
        self.producer_routing_key = producer_routing_key
        self.producer_message_channel = None
        self.proactive_invoke_stop_event = None
        self._link()

    def _link(self):
        if self.producer_message_channel is not None:
            if not self.producer_message_channel.is_closed:
                self.producer_message_channel.close()
                logger.info(
                    f'close channel for producer working on {self.producer_exchange} + {self.producer_routing_key}')
            else:
                logger.info(
                    f'channel for producer working on {self.producer_exchange} + {self.producer_routing_key} has already been closed')
            # self.proactive_invoke_stop_event.set()  # 停止线程

        producer_connection = get_connection_from_config(self.host, self.port, self.username, self.password,
                                                         self.virtual_host, self.heartbeat)
        logger.info(
            f'producer_connection_dict = {producer_connection.__dict__}')
        self.producer_message_channel: pika.adapters.blocking_connection.BlockingChannel = producer_connection.channel()
        logger.info(
            f'producer_channel_dict = {self.producer_message_channel.__dict__}')
        if self.producer_exchange is not None:
            self.producer_message_channel.exchange_declare(exchange=self.producer_exchange,
                                                           exchange_type=self.exchange_type,
                                                           durable=True)

        # # 创建一个Event对象
        # self.proactive_invoke_stop_event: threading.Event = threading.Event()
        # threading.Thread(target=self.proactive_invoke_heartbeat, args=[self.proactive_invoke_stop_event]).start()

    def proactive_invoke_heartbeat(self, stop_event: threading.Event):
        while not stop_event.is_set():
            if self.producer_message_channel is not None and self.producer_message_channel.is_open:
                logger.info(
                    f' proactive_invoke loop {self.producer_exchange} + {self.producer_routing_key} process_data_events')
                self.producer_message_channel._connection.sleep(1.0)

    def sending(self, feedback, exchange=None, routing_key=None):
        super().sending(feedback=feedback)
        exchange = self.producer_exchange if exchange is None else exchange
        routing_key = self.producer_routing_key if routing_key is None else routing_key
        self._produce(feedback, exchange=exchange, routing_key=routing_key)

    def _produce(self, message, exchange=None, routing_key=None):
        logger.debug(
            f'message (type is {type(message)}) sent through Exchange {exchange} and RoutingKey {routing_key}: {message}')
        try:
            self.producer_message_channel.basic_publish(exchange=exchange,
                                                        routing_key=routing_key, body=message)
            logger.debug(
                f'message sent successfully through Exchange {exchange} and RoutingKey {routing_key}')
        except:
            logger.exception('消息发送异常，即将重试')
            self._link()
            try:
                self.producer_message_channel.basic_publish(exchange=exchange,
                                                            routing_key=routing_key, body=message)
                logger.debug(
                    f'message sent successfully through Exchange {exchange} and RoutingKey {routing_key}')
            except:
                logger.exception('消息发送异常，不重试')
