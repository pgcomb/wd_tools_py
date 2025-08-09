from confluent_kafka import Consumer, Producer, KafkaError, KafkaException
import signal
import json
import logging


def value_str(value):
    return value.decode('utf-8')


def value_bytes(value):
    return value


def value_json(value):
    return json.loads(value.decode('utf-8'))


deserializers = {
    'str': value_str,
    'bytes': value_bytes,
    'json': value_json
}


class KafkaMessageIterator:
    def __init__(self, bootstrap_servers, group_id, topic, sasl_plain_username=None, sasl_plain_password=None,
                 security_protocol="SASL_PLAINTEXT", sasl_mechanism="PLAIN", value_deserializer="str", logger=None,
                 conf=None):
        if conf is None:
            conf = {}
        # Kafka 消费者配置
        self.conf = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'max.poll.interval.ms': 3600000,
            'auto.offset.reset': "earliest",
        }
        if sasl_plain_username and sasl_plain_password:
            self.conf['security.protocol'] = security_protocol
            self.conf['sasl.mechanism'] = sasl_mechanism
            self.conf['sasl.username'] = sasl_plain_username
            self.conf['sasl.password'] = sasl_plain_password
        self.conf = {**self.conf, **conf}
        self.consumer = None  # 延迟创建消费者实例
        self.topics = topic if isinstance(topic, list) else topic.split(',')
        self.running = True
        self.logger = logger or logging.getLogger('kafka_consumer')

        self.value_deserializer = deserializers[value_deserializer] if isinstance(value_deserializer,
                                                                                  str) else value_deserializer

        # 注册信号处理，以便优雅退出
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def __enter__(self):
        """进入上下文时调用"""
        # 创建消费者实例
        self.consumer = Consumer(self.conf)
        # 订阅主题
        self.consumer.subscribe(self.topics)
        self.logger.info(f"kafka consume start --> servers:{self.conf['bootstrap.servers']},topics:{self.topics}")
        return self  # 返回自身，以便在 with 语句中使用

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时调用，无论是否发生异常"""
        if self.consumer:
            self.logger.info(f"Closing Kafka({self.conf['bootstrap.servers']}, {self.topics}) consumer...")
            self.consumer.close()
        # 返回 False 表示不抑制异常，让异常正常传播
        # 如果你想在这里处理特定异常并抑制它，可以返回 True
        return False

    def __iter__(self):
        # 已经在 __enter__ 中订阅，直接返回 self
        if not self.consumer:
            raise RuntimeError("Consumer not initialized. Use 'with' statement.")
        return self

    def __next__(self):
        if not self.running:
            raise StopIteration

        if not self.consumer:
            raise RuntimeError("Consumer not initialized.")

        # 轮询消息
        msg = self.consumer.poll(timeout=1.0)

        if msg is None:
            # 没有消息，继续等待
            return self.__next__()

        if msg.error():
            # 处理错误
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # 到达分区末尾，继续等待新消息
                return self.__next__()
            else:
                # 其他错误，抛出异常
                raise KafkaException(msg.error())
        try:
            value = self.value_deserializer(msg.value())
        except:
            self.logger.exception("value deserialize error")
            value = None
        # 成功接收到消息
        return {
            'key': msg.key().decode('utf-8') if msg.key() else None,
            'value': value,
            'topic': msg.topic(),
            'partition': msg.partition(),
            'offset': msg.offset()
        }


class KafkaProducer:
    def __init__(self, bootstrap_servers, sasl_plain_username=None, sasl_plain_password=None,
                 security_protocol="SASL_PLAINTEXT", sasl_mechanism="PLAIN", logger=None,
                 conf=None):
        conf = conf or {}
        self.logger = logger or logging.getLogger('kafka_producer')
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

    def delivery_report(self, err, msg):
        """
        回调函数，用于确认消息是否成功发送。

        :param err: 如果发送失败，则包含错误信息；否则为 None
        :param msg: 包含已发送或尝试发送的消息的详细信息
        """
        if err is not None:
            self.logger.error(f'Message delivery failed: {err}')
        else:
            self.logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

    def send_message(self, topic, value, key=None):
        """
        向指定主题发送消息。

        :param topic: 目标主题名称
        :param key: 消息键（可选）
        :param value: 消息体（必须提供）
        :param value_serializer: 序列化函数，默认将字典转换为 JSON 字符串并编码为 UTF-8
        """
        if value is None:
            raise ValueError("Message value cannot be None")

        # 序列化值
        serialized_key = key.encode('utf-8') if key else None
        serialized_value = value.encode('utf-8') if isinstance(value, str) else json.dumps(value).encode('utf-8')
        try:
            # 异步发送消息
            self.producer.produce(topic, key=serialized_key, value=serialized_value,
                                  callback=self.delivery_report)
        except BufferError:
            self.logger.exception('Local producer queue is full (%d messages awaiting delivery): try again\n' %
                  len(self.producer))
        except KafkaException:
            self.logger.exception(f'Failed to send message.')

        # 等待所有异步消息被发送出去
        self.producer.flush()

    def close(self):
        """确保所有消息都被发送，并关闭生产者"""
        self.producer.flush()


# 使用示例
if __name__ == "__main__":
    # 创建生产者实例
    from aabd.base.log_setting import get_set_once_logger
    producer = KafkaProducer(bootstrap_servers='192.168.0.14:19092',
                sasl_plain_username='admin',
                sasl_plain_password='jdyx#qwe12',
                logger=get_set_once_logger())

    try:
        # 发送消息
        producer.send_message(topic='wdx250809', key='my-key', value={'message': 'Hello, Kafka!'})

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # 关闭生产者
        producer.close()
# 使用示例 (推荐方式)
# if __name__ == "__main__":
#     # 使用 with 语句确保资源被正确管理
#     from aabd.base.log_setting import get_set_once_logger
#
#     try:
#         with KafkaMessageIterator(
#                 bootstrap_servers='192.168.0.14:19092',
#                 group_id='wdx',
#                 topic='wdx250809',
#                 sasl_plain_username='admin',
#                 sasl_plain_password='jdyx#qwe12',
#                 value_deserializer='json',
#                 logger=get_set_once_logger()
#         ) as kafka_iter:
#             for message in kafka_iter:
#                 print(f"Received: {message}")
#                 # 在这里处理你的消息逻辑
#                 # 例如：处理 value, 记录日志等
#                 # 如果你想在某个条件后停止，可以 break
#                 # if some_condition:
#                 #     break
#
#     except KeyboardInterrupt:
#         print("Interrupted by user")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#     # 无论正常结束还是发生异常，连接都会在退出 with 块时关闭
