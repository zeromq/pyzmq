"""Example using zmq with asyncio with pub/sub and dealer/router for asynchronous messages

Publisher sends either 'Hello World' or 'Hello Sekai' based on class language setting,
which is received by the Subscriber

When the Router receives a message from the Dealer, it changes the language setting"""

# Copyright (c) Stef van der Struijk.
# This example is in the public domain (CC-0)

import asyncio
import zmq.asyncio
from zmq.asyncio import Context
import traceback
import logging


# set message based on language
class HelloWorld:
    def __init__(self):
        self.lang = 'eng'
        self.msg = "Hello World"

    def change_language(self):
        if self.lang == 'eng':
            self.lang = 'jap'
            self.msg = "Hello Sekai"

        else:
            self.lang = 'eng'
            self.msg = "Hello World"

    def msg_pub(self):
        return self.msg


# receives "Hello World" from topic 'world'
# changes "World" to "Sekai" and returns message 'sekai'
class HelloWorldPrinter:
    # process received message
    def msg_sub(self, msg):
        print("message received world: {}".format(msg))


# manages message flow between publishers and subscribers
class HelloWorldMessage:
    def __init__(self, url='127.0.0.1', port='5555'):
        # get ZeroMQ version
        print("Current libzmq version is %s" % zmq.zmq_version())
        print("Current  pyzmq version is %s" % zmq.__version__)

        self.url = "tcp://{}:{}".format(url, port)
        # pub/sub and dealer/router
        self.ctx = Context.instance()

        # init hello world publisher obj
        self.hello_world = HelloWorld()

        # activate publishers / subscribers
        asyncio.get_event_loop().run_until_complete(
            asyncio.wait(
                [
                    self.hello_world_pub(),
                    self.hello_world_sub(),
                    self.lang_changer_router(),  # less restrictions than REP
                    self.lang_changer_dealer(),  # less restrictions than REQ
                ]
            )
        )

    # generates message "Hello World" and publish to topic 'world'
    async def hello_world_pub(self):
        pub = self.ctx.socket(zmq.PUB)
        pub.connect(self.url)

        # give time to subscribers to initialize; wait time >.2 sec
        await asyncio.sleep(0.3)
        # send setup connection message
        # await pub.send_multipart([b'world', "init".encode('utf-8')])
        # await pub.send_json([b'world', "init".encode('utf-8')])

        # without try statement, no error output
        try:
            # keep sending messages
            while True:
                # ask for message
                msg = self.hello_world.msg_pub()
                print("world pub: {}".format(msg))

                # slow down message publication
                await asyncio.sleep(0.5)

                # publish message to topic 'world'
                # multipart: topic, message; async always needs `send_multipart()`?
                await pub.send_multipart([b'world', msg.encode('utf-8')])

        except Exception as e:
            print("Error with pub world")
            # print(e)
            logging.error(traceback.format_exc())
            print()

        finally:
            # TODO disconnect pub/sub
            pass

    # processes message topic 'world'; "Hello World" or "Hello Sekai"
    async def hello_world_sub(self):
        print("Setting up world sub")
        obj = HelloWorldPrinter()
        # setup subscriber
        sub = self.ctx.socket(zmq.SUB)
        sub.bind(self.url)
        sub.setsockopt(zmq.SUBSCRIBE, b'world')
        print("World sub initialized")

        # without try statement, no error output
        try:
            # keep listening to all published message on topic 'world'
            while True:
                [topic, msg] = await sub.recv_multipart()
                print("world sub; topic: {}\tmessage: {}".format(topic, msg))
                # process message
                obj.msg_sub(msg.decode('utf-8'))

                # await asyncio.sleep(.2)

                # publish message to topic 'sekai'
                # async always needs `send_multipart()`
                # await pub.send_multipart([b'sekai', msg_publish.encode('ascii')])

        except Exception as e:
            print("Error with sub world")
            # print(e)
            logging.error(traceback.format_exc())
            print()

        finally:
            # TODO disconnect pub/sub
            pass

    # Deal a message to topic 'lang' that language should be changed
    async def lang_changer_dealer(self):
        # setup dealer
        deal = self.ctx.socket(zmq.DEALER)
        deal.setsockopt(zmq.IDENTITY, b'lang_dealer')
        deal.connect(self.url[:-1] + "{}".format(int(self.url[-1]) + 1))
        print("Command dealer initialized")

        # give time to router to initialize; wait time >.2 sec
        await asyncio.sleep(0.3)
        msg = "Change that language!"

        # without try statement, no error output
        try:
            # keep sending messages
            while True:
                print("Command deal: {}".format(msg))

                # slow down message publication
                await asyncio.sleep(2.0)

                # publish message to topic 'world'
                # multipart: topic, message; async always needs `send_multipart()`?
                await deal.send_multipart([msg.encode('utf-8')])

        except Exception as e:
            print("Error with pub world")
            # print(e)
            logging.error(traceback.format_exc())
            print()

        finally:
            # TODO disconnect dealer/router
            pass

    # changes Hello xxx message when a command is received from topic 'lang'; keeps listening for commands
    async def lang_changer_router(self):
        # setup router
        rout = self.ctx.socket(zmq.ROUTER)
        rout.bind(self.url[:-1] + "{}".format(int(self.url[-1]) + 1))
        # rout.setsockopt(zmq.SUBSCRIBE, b'')
        print("Command router initialized")

        # without try statement, no error output
        try:
            # keep listening to all published message on topic 'world'
            while True:
                [id_dealer, msg] = await rout.recv_multipart()
                print(
                    "Command rout; Sender ID: {};\tmessage: {}".format(id_dealer, msg)
                )

                self.hello_world.change_language()
                print(
                    "Changed language! New language is: {}\n".format(
                        self.hello_world.lang
                    )
                )

        except Exception as e:
            print("Error with sub world")
            # print(e)
            logging.error(traceback.format_exc())
            print()

        finally:
            # TODO disconnect dealer/router
            pass


if __name__ == '__main__':
    HelloWorldMessage()
