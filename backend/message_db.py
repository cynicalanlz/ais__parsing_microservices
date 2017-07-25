import asyncio
import aioamqp
import asyncpg
import json
import uvloop
import logging, sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

class DbClient:
    def __init__(self, pool):
        self.pool = pool

    async def on_request(self, channel, body, envelope, properties):
        jsn = json.loads(body.decode('utf-8'))
        qw = jsn.get('query', '')
        qw_type = jsn.get('type', '')
        vals = []  
        resp = {}
        print(qw_type, qw)
        async with self.pool.acquire() as connection:
            # Open a transaction.
            async with connection.transaction():
                # Run the query passing the request argument.
                if qw_type == 'select' and qw:
                    vals = await connection.fetch(qw)
                    resp_vals = [tuple(item) for item in vals]
                    resp = {
                        'message': 'ok',
                        'data' : resp_vals
                    }
                elif qw_type in ['insert', 'delete'] and qw:
                    try:
                        await connection.execute(qw)
                        resp = {
                            'message' : 'ok'
                        }
                    except Exception as e:
                        print(e)
                        resp = {
                            'message' : 'not ok'
                        }
                else:
                    resp = {
                            'message' : 'not ok'
                    }

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

    transport, protocol = await aioamqp.connect()
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