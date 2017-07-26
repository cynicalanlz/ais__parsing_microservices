import sys, logging, json
from logging.handlers import RotatingFileHandler
import asyncio
import aioamqp
import uvloop
from constants import LOGGING_FORMAT, RABBIT
from spider.crawler import Crawler
from db_wrapper.classes import DbRpcClient
from web_service import get_table
import redis

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(LOGGING_FORMAT)
handler = RotatingFileHandler('app.log', maxBytes=2000, backupCount=10)
handler.setFormatter(formatter)
logger.addHandler(handler)

class WebsiteHandler:
    def __init__(self, loop):
        self.loop = loop
        self.redis = redis.ConnectionPool(host='localhost', port=6379, db=0)

    async def timed_crawler(self, url, freq, ws_id):
        redis_conn = redis.Redis(connection_pool=self.redis)

        while True:
            ws_freq_check = redis_conn.get(ws_id)

            if not ws_freq_check or not int(ws_freq_check) >= 0:
                logging.info('got shutdown signal {}'.format(str(ws_id)))
                break

            crawler = Crawler([url], loop=self.loop, db_rpc=DbRpcClient())
            await crawler.crawl()
            crawler.close()

            await asyncio.sleep(int(freq) * 60)


    async def one_time_crawler(self, url, freq, ws_id):
      
        crawler = Crawler([url], loop=self.loop, db_rpc=DbRpcClient())
        await crawler.crawl()
        crawler.close()

                
    async def callback(self, channel, body, envelope, properties):

        logging.info('in callback')  
        jsn = json.loads(body.decode('utf-8'))
        logging.info(jsn)
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

        if jsn:
            for key in ['url', 'freq', 'ws_id']:
                if key not in jsn:
                    return

        url = jsn['url']
        freq = int(jsn['freq'])
        ws_id = int(jsn['ws_id'])

        if freq == 0:
            return asyncio.Task(self.one_time_crawler(url, freq, ws_id), loop=self.loop)
        else:
            return asyncio.Task(self.timed_crawler(url, freq, ws_id), loop=self.loop)
        
        
    async def worker(self):
        ws = await get_table('websites')
        workers = []
        redis_conn = redis.Redis(connection_pool=self.redis)
        
        for website in ws:
            workers.append(asyncio.Task(self.timed_crawler(website[1], website[2], website[0]), loop=self.loop))
            redis_conn.set(website[0], website[2])
    
        try:
            transport, protocol = await aioamqp.connect(**RABBIT)
        except aioamqp.AmqpClosedConnection:
            print("closed connections")
            return

        channel = await protocol.channel()
        await channel.queue(queue_name='ws_queue', durable=True)
        await channel.basic_qos(prefetch_count=1, prefetch_size=0, connection_global=False)
        await channel.basic_consume(self.callback, queue_name='ws_queue')

if __name__=='__main__':
    loop = asyncio.get_event_loop()
    # loop = uvloop.new_event_loop()
    # asyncio.set_event_loop(loop)
    ws_handler = WebsiteHandler(loop)
    loop.run_until_complete(ws_handler.worker())
    loop.run_forever()