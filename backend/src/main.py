import asyncio
import logging
from multiprocessing import Process, Queue
from multiprocessing.queues import Queue as MPQueue

import uvicorn

from core.events import CoreEvent, DeploymentEvent
from infra import DeploymentConsumer, PositionRelay


logger = logging.getLogger(__name__)


def main0():
    uvicorn.run("server.app:app", port=8000, host="localhost", reload=True)


def run_server(queue) -> None:
    global logger

    logger.info("Starting server.")
    import config

    config.DEPLOYMENT_QUEUE = queue
    uvicorn.run("server.app:app", port=8000, host="localhost")


def handle_deployment_consumer(queue: MPQueue) -> None:
    consumer = DeploymentConsumer()

    while True:
        ev: CoreEvent[DeploymentEvent] = queue.get_nowait()
        consumer.consume(ev.data)


async def main1():
    global logger

    queue = Queue()

    pargs = (
        (run_server, (queue,), {}, "Server"),
        (handle_deployment_consumer, (queue,), {}, "Deployment Consumer"),
        (PositionRelay().listen, (), {}, "Positions Relay"),
    )

    ps = [
        Process(target=target, args=args, kwargs=kwargs, name=name)
        for target, args, kwargs, name in pargs
    ]

    for p in ps:
        p.start()

    try:
        while True:
            for ind, p in enumerate(ps):
                if not p.is_alive():
                    logger.info(f"Process {p.name} has died")
                    p.kill()
                    p.join()

                    logger.info(f"Relaunching process {p.name}.")

                    target, args, kwargs, name = pargs[ind]
                    new_p = Process(target=target, args=args, kwargs=kwargs, name=name)
                    new_p.start()
                    ps[ind] = new_p

                    logger.info(f"Process {p.name} has beeen relaunched successfully.")

            await asyncio.sleep(0.1)
    except BaseException:
        pass
    finally:
        for p in ps:
            p.kill()
            p.join()


if __name__ == "__main__":
    main0()
    # asyncio.run(main1())
