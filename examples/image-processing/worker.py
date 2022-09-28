import multiprocessing as mp
from os import path
from typing import Tuple

from log import logger
from PIL import Image

import zmq


def process_images(
    size: Tuple[int, int],
    worker_id: int,
    router_address: str,
    publisher_address: str,
    path2resized_images: str,
    worker_arrival: mp.Value,
    arrival_condition: mp.Condition,
    server_liveness: mp.Event,
    workers_synchronizer: mp.Barrier,
):

    ZEROMQ_INIT = 0
    try:
        ctx: zmq.Context = zmq.Context()
        dealer_socket: zmq.Socket = ctx.socket(zmq.DEALER)
        subscriber_socket: zmq.Socket = ctx.socket(zmq.SUB)

        dealer_socket.connect(router_address)
        subscriber_socket.connect(publisher_address)
        subscriber_socket.set(zmq.SUBSCRIBE, b'')  # subscribe to all topics

        ZEROMQ_INIT = 1

        poller = zmq.Poller()
        poller.register(dealer_socket, zmq.POLLIN)
        poller.register(subscriber_socket, zmq.POLLIN)

        liveness_value = server_liveness.wait(
            timeout=10
        )  # wait atleast 10s for server to be ready
        if not liveness_value:
            logger.error(f'worker {worker_id:03d} wait too long for server to be ready')
            exit(1)

        arrival_condition.acquire()
        with worker_arrival.get_lock():
            worker_arrival.value += 1
            logger.debug(
                f'worker {worker_id:03d} has established connection with {router_address} and {publisher_address}'
            )
        arrival_condition.notify_all()
        arrival_condition.release()

        logger.debug(f'worker {worker_id:03d} is waiting at the barrier')
        workers_synchronizer.wait(timeout=5)  # wait at the barrier

        worker_status = 0  # 0 => free | 1 => busy
        keep_loop = True
        while keep_loop:
            if not server_liveness.is_set():
                logger.warning(f'server is down...! worker {worker_id:03d} will stop')
                break

            if worker_status == 0:
                dealer_socket.send_multipart([b'', b'req', b''])  # ask a job
                worker_status = 1  # worker is busy

            incoming_events = dict(poller.poll(100))
            dealer_poller_status = incoming_events.get(dealer_socket, None)
            subscriber_poller_status = incoming_events.get(subscriber_socket, None)
            if dealer_poller_status is not None:
                if dealer_poller_status == zmq.POLLIN:
                    try:
                        _, encoded_path2image = dealer_socket.recv_multipart()
                        path2source_image = encoded_path2image.decode()
                        image = Image.open(path2source_image)
                        resized_image = image.resize(size=size)
                        _, filename = path.split(path2source_image)
                        path2target_image = path.join(path2resized_images, filename)
                        resized_image.save(path2target_image)
                        dealer_socket.send_multipart([b'', b'rsp'], flags=zmq.SNDMORE)
                        dealer_socket.send_pyobj(
                            {
                                'incoming_image': path2source_image,
                                'worker_id': worker_id,
                                'status': 1,
                            }
                        )
                    except Exception as e:
                        logger.error(e)
                        logger.error(
                            f'worker {worker_id:03d} was not able to process : {path2source_image}'
                        )
                        dealer_socket.send_multipart([b'', b'rsp'], flags=zmq.SNDMORE)
                        dealer_socket.send_pyobj(
                            {
                                'incoming_image': path2source_image,
                                'worker_id': worker_id,
                                'status': 0,
                            }
                        )
                    worker_status = 0  # worker is free => can ask a new job

            if subscriber_poller_status is not None:
                if subscriber_poller_status == zmq.POLLIN:
                    topic, _ = subscriber_socket.recv_multipart()
                    if topic == b'quit':
                        logger.debug(
                            f'worker {worker_id:03d} got the quit signal from server'
                        )
                        keep_loop = False
        # end while loop ...!

    except KeyboardInterrupt:
        pass
    except Exception as e:
        if workers_synchronizer.broken:
            logger.warning(
                f'worker {worker_id:03d} will stop. the barrier was broken by some workers'
            )
        else:
            logger.error(e)
    finally:
        if ZEROMQ_INIT == 1:
            poller.unregister(subscriber_socket)
            poller.unregister(dealer_socket)

            subscriber_socket.close()
            dealer_socket.close()

            ctx.term()

        logger.info(f'worker {worker_id:03d} has released all zeromq ressources')
