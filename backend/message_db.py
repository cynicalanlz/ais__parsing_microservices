import asyncio
import aioamqp
import asyncpg
import json
import uvloop
import logging, sys
from constants import RABBIT

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)
import datetime

class DbClient:
    def __init__(self, pool):
        self.pool = pool

    async def on_request(self, channel, body, envelope, properties):
        jsn = json.loads(body.decode('utf-8'))
        qw = jsn.get('query', '')
        qw_type = jsn.get('type', '')
        vals = []  
        resp = {}
        async with self.pool.acquire() as connection:
            # Open a transaction.
            async with connection.transaction():
                # Run the query passing the request argument.
                if qw_type == 'select' and qw:
                    try:
                        vals = await connection.fetch(qw)
                    except Exception as e:
                        logging.error(e)
                        resp = {
                            'message' : 'not ok'
                        }
                    resp_vals = [list(tuple(item)) for item in vals]
                    for q in range(len(resp_vals)):
                        item = resp_vals[q]
                        for i in range(len(item)):
                            it = item[i]
                            if isinstance(it,datetime.datetime):
                                resp_vals[q][i] = it.strftime("%Y-%m-%d %H:%M:%S")

                    resp = {
                        'message': 'ok',
                        'data' : resp_vals
                    }
                    
                elif qw_type in ['insert_returning'] and qw:
                    data = await connection.fetchval(qw)
                    logging.info(data)
                    resp = {
                        'message' : 'ok',
                        'data' : data
                    }

                elif qw_type in ['insert', 'delete'] and qw:
                    try:
                        await connection.execute(qw)
                        resp = { 'message' : 'ok' }
                    except Exception as e:
                        logging.error(e)
                        resp = { 'message' : 'not ok' }
                else:
                    resp = { 'message' : 'ok' }

        await channel.basic_publish(
            payload=json.dumps(resp),
            exchange_name='',
            routing_key=properties.reply_to,
            properties={
                'correlation_id': properties.correlation_id,
            },
        )
        
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)        

async def rpc_server():

    transport, protocol = await aioamqp.connect(**RABBIT)
    channel = await protocol.channel()
    pool = await asyncpg.create_pool(
        database='aiopg',
        user='aiopg',
        password='aiopg',
        host='127.0.0.1'
        )

    client = DbClient(pool)

    await channel.queue_declare(queue_name='db_queue')
    await channel.basic_qos(prefetch_count=1, prefetch_size=0, connection_global=False)
    await channel.basic_consume(client.on_request, queue_name='db_queue')
    print(" [x] Awaiting RPC requests")

if __name__=='__main__':
    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(rpc_server())
    loop.run_forever()