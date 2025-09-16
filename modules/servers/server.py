import asyncio
from modules.servers.wss_server import start_server, latest_frames
from modules.servers.frame_parser import show_frames, the_frame
from modules.servers.http_server import start_http_server


async def task_manager():
    task1 = asyncio.create_task(start_server())
    task2 = asyncio.create_task(show_frames(latest_frames))
    task3 = asyncio.create_task(start_http_server())

    tasks = [task1, task2, task3]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        # تسک‌ها لغو شدن، نیازی به لاگ اضافی نیست
        pass


def main():
    try:
        asyncio.run(task_manager())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")


if __name__ == "__main__":
    main()
