import asyncio
import aioamqp
import uuid

class DbRpcClient(object):
    def __init__(self):
        self.transport = None
        self.protocol = None
        self.channel = None
        self.callback_queue = None
        self.waiter = asyncio.Event()

    async def connect(self):
        """ an `__init__` method can't be a coroutine"""
        self.transport, self.protocol = await aioamqp.connect(login='rabbitmq', password='rabbitmq')
        self.channel = await self.protocol.channel()

        result = await self.channel.queue_declare(queue_name='', exclusive=True)
        self.callback_queue = result['queue']

        await self.channel.basic_consume(
            self.on_response,
            no_ack=True,
            queue_name=self.callback_queue,
        )

    async def on_response(self, channel, body, envelope, properties):
        if self.corr_id == properties.correlation_id:
            self.response = body

        self.waiter.set()

    async def call(self, db_query):
        if not self.protocol:
            await self.connect()
        self.response = None
        self.corr_id = str(uuid.uuid4())
        await self.channel.basic_publish(
            payload=db_query,
            exchange_name='',
            routing_key='db_queue',
            properties={
                'reply_to': self.callback_queue,
                'correlation_id': self.corr_id,
            },
        )
        await self.waiter.wait()

        await self.protocol.close()
        return self.response
