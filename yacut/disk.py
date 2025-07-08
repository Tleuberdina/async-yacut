import asyncio
import os
from urllib.parse import quote
import aiohttp

from . import app


AUTH_HEADERS = {
    'Authorization': f'OAuth {app.config["DISK_TOKEN"]}'
}

DISK_INFO_URL = (
    f'{app.config["API_HOST"]}'
    f'{app.config["API_VERSION"]}'
    '/disk/'
)
DOWNLOAD_LINK_URL = (
    f'{app.config["API_HOST"]}'
    f'{app.config["API_VERSION"]}'
    '/disk/resources/download'
)
REQUEST_UPLOAD_URL = (
    f'{app.config["API_HOST"]}'
    f'{app.config["API_VERSION"]}'
    '/disk/resources/upload'
)


async def async_upload_files_to_disk(files):
    """
    Асинхронная функция, которая создаёт задачи и запускает их.
    """
    if files is not None:
        tasks = []
        async with aiohttp.ClientSession() as session:
            for file in files:
                tasks.append(
                    asyncio.ensure_future(
                        upload_file_and_get_url(session, file)
                    )
                )
            download_info = await asyncio.gather(*tasks)
        return download_info


async def upload_file_and_get_url(session, file):
    """
    Асинхронная функция загрузки изображений и получения на них ссылок.
    """
    filename = file.filename
    file.save(filename)
    payload = {
        'path': f'app:/{quote(filename)}',
        'overwrite': 'true'
    }
    async with session.get(
        REQUEST_UPLOAD_URL,
        headers=AUTH_HEADERS,
        params=payload
    ) as response:
        response.raise_for_status()
        upload_data = await response.json()
        upload_url = upload_data['href']
    with open(filename, 'rb') as f:
        async with session.put(
            upload_url,
            data=f,
            headers=AUTH_HEADERS
        ) as upload_response:
            upload_response.raise_for_status()
    async with session.get(
        DOWNLOAD_LINK_URL,
        headers=AUTH_HEADERS,
        params={'path': f'app:/{filename}'}
    ) as download_response:
        download_response.raise_for_status()
        download_data = await download_response.json()
        return {
            'name': filename,
            'url': download_data['href']
        }
    os.remove(filename)
