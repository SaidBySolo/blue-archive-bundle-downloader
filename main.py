import asyncio
import os
from typing import Optional

import inquirer
from aiofile.utils import async_open
from aiohttp import ClientSession

netloc = "ba.dn.nexoncdn.co.kr"


async def request(url: str, json: Optional[dict[str, str]] = None):
    async with ClientSession() as cs:
        if json:
            async with cs.post(url, json=json) as r:
                return await r.json()

        async with cs.get(url) as r:
            return await r.json(content_type=None)


async def download(url: str, path: str):
    async with ClientSession() as cs:
        async with cs.get(url) as r:
            async with async_open(path, "wb") as f:
                async for data, _ in r.content.iter_chunks():
                    await f.write(data)


async def main():
    r = await request(
        "https://api-pub.nexon.com/patch/v1.1/version-check",
        json={
            "country": "KR",
            "market_game_id": "1571873795",
            "language": "ko-KR",
            "curr_build_version": "1.35.115378",
            "market_code": "appstore",
            "sdk_version": "103",
            "curr_build_number": "115378",
        },
    )

    resource_path = r["patch"]["resource_path"]

    resource_data = await request(resource_path)

    bundles = filter(
        lambda item: "GameData" == item["group"]
        and item["resource_path"].endswith(".bundle"),
        resource_data["resources"],
    )

    find = [
        inquirer.Text(
            "find",
            message="Search for the bundle you want to download. If you want to download all, please enter all.",
        )
    ]

    query: str = inquirer.prompt(find)["find"]

    if query.lower() == "all":
        if not os.path.exists("./bundles"):
            os.makedirs("./bundles")

        return await asyncio.wait(
            [
                download(
                    f"https://{netloc}/{item['resource_path']}",
                    f"./bundles/{item['resource_path'].replace('GameData/iOS/', '')}",
                )
                for item in bundles
            ]
        )

    searched_list = list(
        filter(lambda item: query.lower() in item["resource_path"], bundles)
    )

    bundle_choices = [
        inquirer.Checkbox(
            "choices",
            message="Select the file you want to download. You can use the space key to select",
            choices=[searched["resource_path"] for searched in searched_list],
        ),
    ]

    choiced: list[str] = inquirer.prompt(bundle_choices)["choices"]

    if not os.path.exists("./bundles"):
        os.makedirs("./bundles")

    await asyncio.wait(
        [
            download(
                f"https://{netloc}/{item}",
                f"./bundles/{item.replace('GameData/iOS/', '')}",
            )
            for item in choiced
        ]
    )


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
