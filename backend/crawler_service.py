import sys, logging
from logging.handlers import RotatingFileHandler
import asyncio
import aioamqp
import uvloop
from constants import LOGGING_FORMAT, RABBIT
from spider.crawler import Crawler
from db_wrapper.classes import DbRpcClient
from web_service import get_table

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(LOGGING_FORMAT)
handler = RotatingFileHandler('app.log', maxBytes=2000, backupCount=10)
handler.setFormatter(formatter)
logger.addHandler(handler)

class WebsiteHandler:
    def __init__(self, loop):
        self.loop = loop

    async def timed_crawler(self, url, freq):
        while True:
            crawler = Crawler([url], loop=self.loop, db_rpc=DbRpcClient())     
            await crawler.crawl()
            crawler.close()
            if freq > 0:
                await asyncio.sleep(int(freq) * 10)
            else:
                return

    async def callback(self, channel, body, envelope, properties):    
        
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

    async def worker(self):
        try:
            transport, protocol = await aioamqp.connect(**RABBIT)
        except aioamqp.AmqpClosedConnection:
            print("closed connections")
            return

        ws = await get_table('websites')

        workers = []

        for website in ws:
            workers.append(asyncio.Task(self.timed_crawler(website[1], website[2]), loop=self.loop))

        channel = await protocol.channel()
        
        await channel.queue(queue_name='ws_queue', durable=True)
        await channel.basic_qos(prefetch_count=1, prefetch_size=0, connection_global=False)
        await channel.basic_consume(self.callback, queue_name='ws_queue')

if __name__=='__main__':
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)

    ws_handler = WebsiteHandler(loop)

    loop.run_until_complete(ws_handler.worker())
    loop.run_forever()


