import logging

logger = logging.getLogger(__name__)


class MqSender:
    def __init__(self):
        pass

    # to override
    def sending(self, feedback, **kwargs):
        logger.debug(f'发送数据（type is {type(feedback)}）: {feedback}')


class MqReceiver:

    def __init__(self):
        self.__callback = None

    def set_callback(self, callback):
        self.__callback = callback
        logger.info('mq receiver 设置回调完成')

    def _receive(self, message, **kwargs):
        try:
            if isinstance(message, bytes):
                logger.debug(f'接收bytes数据（type is {type(message)}），待转化: {message}')
                message = message.decode('utf-8')
            logger.debug(f'接收数据（type is {type(message)}）: {message}')
            if self.__callback is None:
                logger.info('callback未定义')
            else:
                self.__callback(message, **kwargs)
        except:
            logger.error('消息处理异常', exc_info=True, stack_info=True)

    # to override
    def start_receiving(self):
        logger.info('mq receiver 准备开始工作')
