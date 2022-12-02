import time

from anyio import to_thread, run


def sleep(sec: int = 3):
    print(f'Start: sleep for {sec} sec...')
    time.sleep(sec)
    print('Finish: sleep for {sec} sec.')


async def main():
    await to_thread.run_sync(sleep, 5)
    await to_thread.run_sync(sleep, 5)
    await to_thread.run_sync(sleep, 5)


run(main)
