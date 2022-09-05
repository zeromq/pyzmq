import multiprocessing as mp
import pickle
import time
from glob import glob
from os import path
from typing import List, Tuple

import click
import cv2
from loguru import logger
from worker import process_images

import zmq

"""
    ZMQ client-server for parallel image processing(resize).
    The server(router) create n workers(dealer): 
        # each worker can ask a job to the server
        # a job is an image to resize and a path where the resized_image will be saved  
        # once, the image was resied, the worker can ask a new job 
        # server will keep sending job to workers until there is no images left or user hit ctl+c 
    NOTE: opencv, numpy, click, loguru must be installed 
"""

"""
    This program has two mode : 
        # sequential
            python main.py sequential-processing --path2initial_images /path/to/source/images --path2resized_images /path/to/target/images --image_extension '*.jpg' --size 512 512
        # parallel 
            python main.py parallel-processing --path2initial_images /path/to/source/images --path2resized_images /path/to/target/images --image_extension '*.jpg' --nb_workers 8 --size 512 512
    parallel mode can be 10x times faster than sequential mode 
"""


@click.group(chain=False, invoke_without_command=True)
@click.pass_context
def cmd_group(clk: click.Context):
    subcommand = clk.invoked_subcommand
    if subcommand is not None:
        logger.debug(f'{subcommand} was called')
    else:
        logger.debug('use --help to see availables subcommands')


@cmd_group.command()
@click.option(
    '--path2initial_images', help='initial images location', type=click.Path(True)
)
@click.option(
    '--path2resized_images', help='resized images location', type=click.Path(True)
)
@click.option(
    '--image_extension', help='image file extension', default='*.jpg', type=str
)
@click.option(
    '--size', help='new image size', type=click.Tuple([int, int]), default=(512, 512)
)
@click.pass_context
def sequential_processing(
    clk: click.Context,
    path2initial_images: click.Path(True),
    path2resized_images: click.Path(True),
    image_extension: str,
    size: Tuple[int, int],
):
    image_filepaths: List[str] = sorted(
        glob(path.join(path2initial_images, image_extension))
    )
    nb_images = len(image_filepaths)
    logger.debug(f'{nb_images:05d} were found at {path2initial_images}')
    start = time.time()
    for cursor, path2source_image in enumerate(image_filepaths):
        bgr_image = cv2.imread(path2source_image)
        resized_image = cv2.resize(bgr_image, dsize=size)
        _, filename = path.split(path2source_image)
        path2target_image = path.join(path2resized_images, filename)
        cv2.imwrite(path2target_image, resized_image)
        print(resized_image.shape, f'{cursor:04d} images')

    end = time.time()
    duration = int(round(end - start))
    logger.success(
        f'server has processed {cursor:04d}/{nb_images} images in {duration:03d}s'
    )


@cmd_group.command()
@click.option(
    '--path2initial_images', help='initial images location', type=click.Path(True)
)
@click.option(
    '--path2resized_images', help='resized images location', type=click.Path(True)
)
@click.option(
    '--image_extension', help='image file extension', default='*.jpg', type=str
)
@click.option(
    '--nb_workers', help='number of workers to process images', default=2, type=int
)
@click.option(
    '--size', help='new image size', type=click.Tuple([int, int]), default=(512, 512)
)
@click.pass_context
def parallel_processing(
    clk: click.Context,
    path2initial_images: click.Path(True),
    path2resized_images: click.Path(True),
    image_extension: str,
    nb_workers: int,
    size: Tuple[int, int],
):
    ZEROMQ_INIT = 0
    WORKER_INIT = 0
    try:
        router_address = 'ipc://router.ipc'
        publisher_address = 'ipc://publisher.ipc'

        ctx: zmq.Context = zmq.Context()
        router_socket: zmq.Socket = ctx.socket(zmq.ROUTER)
        publisher_socket: zmq.Socket = ctx.socket(zmq.PUB)

        router_socket.bind(router_address)
        publisher_socket.bind(publisher_address)
        ZEROMQ_INIT = 1

        image_filepaths: List[str] = sorted(
            glob(path.join(path2initial_images, image_extension))
        )
        nb_images = len(image_filepaths)
        logger.debug(f'{nb_images:05d} were found at {path2initial_images}')

        if nb_images == 0:
            raise Exception(f'{path2initial_images} is empty')

        workers_acc = []
        server_liveness = mp.Event()
        worker_arrival = mp.Value('i', 0)
        arrival_condition = mp.Condition()
        workers_synchronizer = mp.Barrier(nb_workers)
        for worker_id in range(nb_workers):
            worker_ = mp.Process(
                target=process_images,
                kwargs={
                    'size': size,
                    'worker_id': worker_id,
                    'router_address': router_address,
                    'publisher_address': publisher_address,
                    'worker_arrival': worker_arrival,
                    'server_liveness': server_liveness,
                    'arrival_condition': arrival_condition,
                    'workers_synchronizer': workers_synchronizer,
                    'path2resized_images': path2resized_images,
                },
            )

            workers_acc.append(worker_)
            workers_acc[-1].start()

        WORKER_INIT = 1
        arrival_condition.acquire()
        server_liveness.set()  # send signal to worker
        arrival_condition.wait_for(
            predicate=lambda: worker_arrival.value == nb_workers, timeout=10
        )

        if worker_arrival.value != nb_workers:
            logger.error('server wait to long for worker to be ready')
            exit(1)

        logger.success('all workers are up and ready to process images')
        cursor = 0
        keep_loop = True
        start = time.time()
        while keep_loop:
            socket_id, _, msgtype, message = router_socket.recv_multipart()
            if msgtype == b'req':
                if cursor < nb_images:
                    path2source_image = image_filepaths[cursor]
                    router_socket.send_multipart(
                        [socket_id, b'', path2source_image.encode()]
                    )
                    cursor = cursor + 1
            if msgtype == b'rsp':
                content = pickle.loads(message)
                if content['status'] == 1:
                    print(f"{content['worker_id']:03d}", f"{cursor:04d} items")
            keep_loop = cursor < nb_images
        # end loop over images
        end = time.time()
        duration = int(round(end - start))
        logger.success(
            f'server has processed {cursor:04d}/{nb_images} images in {duration:03d}s'
        )
    except Exception as e:
        logger.error(e)
    finally:
        if WORKER_INIT:
            logger.debug('server is waiting for worker to quit the loop')
            publisher_socket.send_multipart([b'quit', b''])
            for worker_ in workers_acc:
                worker_.join()

        if ZEROMQ_INIT == 1:
            publisher_socket.close()
            router_socket.close()
            ctx.term()

        logger.success('server has released all zeromq ressources')


if __name__ == '__main__':
    cmd_group()
