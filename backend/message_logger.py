import asyncio
import aioamqp
import sys, logging
from constants import LOGGING_FORMAT
import uvloop

import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(LOGGING_FORMAT)
handler = RotatingFileHandler('app.log', maxBytes=2000, backupCount=10)
handler.setFormatter(formatter)
logger.addHandler(handler)


async def callback(channel, body, envelope, properties):    
    logger.info(body)
    await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

async def worker():
    try:
        transport, protocol = await aioamqp.connect(**RABBIT)
    except aioamqp.AmqpClosedConnection:
        print("closed connections")
        return

    channel = await protocol.channel()

    await channel.queue(queue_name='logs_queue', durable=True)
    await channel.basic_qos(prefetch_count=1, prefetch_size=0, connection_global=False)
    await channel.basic_consume(callback, queue_name='logs_queue')

if __name__=='__main__':
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(worker())
    loop.run_forever()


