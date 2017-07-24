from spider.crawler import Crawler
import asyncio
import argparse
from aiohttp import web
import aiohttp_jinja2
import jinja2
import json
import logging, sys, os
import aioamqp

parser = argparse.ArgumentParser(description="aiohttp server")
parser.add_argument('--port')

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


class Handler:

    def __init__(self):
        pass

    async def front(self, request):

        ws = [
            ('http://google.com', 21, 0)
        ]

        context = {
            'title' : 'Website processing queue',
            'websites' : ws

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

        logging.info(url)
        logging.info(freq)

        return web.HTTPFound('/')

    async def handle_delete(self, request):
        name = request.match_info.get('id', "Anonymous")
        txt = "Hello, {}".format(name)
        return web.Response(text=txt)


    async def handle_log(message):
        try:
            transport, protocol = await aioamqp.connect('localhost', 5672)
        except aioamqp.AmqpClosedConnection:
            print("closed connections")
            return


        channel = await protocol.channel()

        await channel.queue('logs_queue', durable=True)

        message = message or "empty message"

        await channel.basic_publish(
            payload=message,
            exchange_name='',
            routing_key='logs_queue',
            properties={
                'delivery_mode': 2,
            },
        )
        print(" [x] Sent %r" % message,)

        await protocol.close()
        transport.close()


def init_app():    
    app = web.Application()
    handler = Handler()
    app.router.add_get('/', handler.front)
    app.router.add_get('/api/v1/create', handler.handle_create)
    app.router.add_get('/api/v1/delete', handler.handle_delete)
    app.router.add_get('/api/v1/log', handler.handle_log)

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