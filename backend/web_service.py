import asyncio
import argparse
from aiohttp import web
import aiohttp_jinja2
import jinja2
import json
import logging, sys, os
from constants import RABBIT

parser = argparse.ArgumentParser(description="aiohttp server")
parser.add_argument('--port')

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


from db_wrapper.classes import DbRpcClient

async def get_table(table_name):
    qw = {
        'type'  : 'select', 
        'query' : 'SELECT * from {};'.format(table_name)
    }

    db_rpc = DbRpcClient()
    db_response = await db_rpc.call(json.dumps(qw))
    jsn = json.loads(db_response.decode('utf-8'))
    ws = []
    for item in jsn.get('data',[]):
        ws.append(tuple(item))
    return ws


async def add_crawler_task(url,freq):    
    qw = {
        'url' : url,
        'freq' : freq
    }

    message = json.dumps(qw)
 
    try:
        transport, protocol = await aioamqp.connect(**RABBIT)
    except aioamqp.AmqpClosedConnection:
        logging.info("closed connections")
        return

    channel = await protocol.channel()

    await channel.queue('ws_queue', durable=True)

    await channel.basic_publish(
        payload=message,
        exchange_name='',
        routing_key='ws_queue',
        properties={
            'delivery_mode': 2,
        },
    )        

    await protocol.close()
    transport.close()

    return


class Handler:

    def __init__(self):
        pass

    async def front(self, request):

        ws = await get_table('websites')
        crawls = await get_table('crawls')

        context = {
            'title' : 'Website processing queue',
            'websites' : ws,
            'crawls' : crawls

        }
        response = aiohttp_jinja2.render_template(
            "index.html",
            request,
            context
            )
        response.headers['Content-Language'] = 'en'
        return response

    async def handle_create(self, request):        
        url = request.query.get('website__name', '')
        freq = request.query.get('website__freq', 0)

        if not freq or not url:
            rsp = json.dumps(
                { 'error' : 'frequency or url not set'}
            )
            return web.Response(text=rsp)

        qw = {
            'type'  : 'insert', 
            'query' : "INSERT INTO websites (url, freq) VALUES ('{}',{});".format(url,freq)
        }

        db_rpc = DbRpcClient()
        db_response = await db_rpc.call(json.dumps(qw))
        jsn = json.loads(db_response.decode('utf-8'))
        
        if jsn['message'] == 'ok':
            logging.info(url)
            logging.info(freq)

        # add task for crawler processing


        await add_crawler_task(url, freq)
                
        return web.HTTPFound('/')

    async def handle_delete(self, request):
        ws_id = request.query.get('id', '')        

        if not ws_id:
            return web.Response(text='no id')
        qw = {
            'type'  : 'delete', 
            'query' : "DELETE from websites where id={}".format(ws_id)
        }
        print(qw)

        db_rpc = DbRpcClient()
        db_response = await db_rpc.call(json.dumps(qw))
        jsn = json.loads(db_response.decode('utf-8'))

        if jsn['message'] == 'ok':
            logging.info('Deleted' + ws_id)
        
        return web.HTTPFound('/')

    async def handle_log(self, request):
        message= request.query.get('message', '')


        if not message:
            rsp = json.dumps(
                { 'error' : 'no message set'}
            )
            return web.Response(text=txt)

        try:
            transport, protocol = await aioamqp.connect(**RABBIT)
        except aioamqp.AmqpClosedConnection:
            logging.info("closed connections")
            return


        channel = await protocol.channel()

        await channel.queue('logs_queue', durable=True)

        await channel.basic_publish(
            payload=message,
            exchange_name='',
            routing_key='logs_queue',
            properties={
                'delivery_mode': 2,
            },
        )        

        await protocol.close()
        transport.close()

        return web.Response(text='ok')


    async def handle_refresh(self, request):
        ws_id= request.query.get('id', '')
        return web.HTTPFound('/')


def init_app():    
    app = web.Application()
    handler = Handler()
    app.router.add_get('/', handler.front)
    app.router.add_get('/api/v1/create', handler.handle_create)
    app.router.add_get('/api/v1/delete', handler.handle_delete)
    app.router.add_get('/api/v1/log', handler.handle_log)
    app.router.add_get('/api/v1/refresh', handler.handle_refresh)

    return app

def get_port(args):
    port = 8080
    if args.port:
        try:
            port = int(args.port)
        except ValueError:
            logging.error('port not integer')
    return port

if __name__ == '__main__':
    args = parser.parse_args()
    app = init_app()

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))
    web.run_app(app, host='127.0.0.1', port=get_port(args))
