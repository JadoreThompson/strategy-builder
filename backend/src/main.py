import asyncio
import logging
import multiprocessing
from multiprocessing import Process

import uvicorn

from workers import deployment_queue_listener, positions_logger, run_server


logger = logging.getLogger(__name__)


def main0():
    uvicorn.run("server.app:app", port=80, host="localhost", reload=True)


async def main1():
    global logger
    
    queue = multiprocessing.Queue()

    pargs = (
        (run_server, (queue,), {}, "Server"),
        (deployment_queue_listener, (queue,), {}, "Deployment queue listener"),
        (positions_logger, (), {}, "Positions logger")
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
