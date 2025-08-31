import aiohttp


async def depends_http_sess():
    async with aiohttp.ClientSession() as sess:
        yield sess
