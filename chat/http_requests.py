import httpx
from typing import List

from settings import MAIN_SERVER_URL


async def get_user_info(_uuid):
    url = MAIN_SERVER_URL + '/api/authentication/v1/user_profile/{}'
    return await request_get(url.format(_uuid), [200])


async def get_list_users_info(users_uuid: List[str]):
    url = MAIN_SERVER_URL + '/api/authentication/v1/users_profiles/'
    return await request_post(url, [200], users_uuid)


async def request_get(url, success_codes: list):
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code in success_codes:
            return r.json()
    return None


async def request_post(url, success_codes: list, data: dict):
    async with httpx.AsyncClient() as client:
        r = await client.post(url, data=data)
        if r.status_code in success_codes:
            return r.json()
    return None
