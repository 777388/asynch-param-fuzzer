import random
import requests
import re
import sys
import asyncio
import aiohttp
import math

print("python3 paramfuzz.py domain")
domain = sys.argv[1]

try:
    # Wayback CDX API
    url = f"http://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&fl=original&collapse=urlkey"
    response = requests.get(url)
    wayback_urls = response.json()

    # CommonCrawl
    url = f"https://index.commoncrawl.org/CC-MAIN-2022-22-index?url=*.{domain}/*&output=json"
    response = requests.get(url)
    commoncrawl_urls = response.json()

    url_list = wayback_urls + commoncrawl_urls
    error_causing_chars = [
        '\n', '\t', '&', '%', '#', '"', "'", ' ', '\\',
        '<', '>', '(', ')', '{', '}', '[', ']', ';', ':', 
        '/', '\\', '@', '$', '!', '*', '+', ',', '.', '?', 
        '^', '_', '~'
    ]
    batch_size = 20
    param_set = set()

    def create_fuzz_string(length):
        fuzz_string = ""
        for i in range(length):
            fuzz_string += random.choice(error_causing_chars)
        return fuzz_string

    async def fetch(session, url, param_name, fuzz_string):
        async with session.get(url, params={param_name: fuzz_string}) as response:
            if response.status >= 400:
                print("\033[91m" + str(response.status) + "\033[0m", "\033[97m" + url + "\033[0m")

    async def main(batch):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in batch:
                try:
                    # Split the URL by '?' to separate the base URL from the parameters
                    base_url, params = url.split('?')

                    # Split the parameters by '&' to separate individual parameters
                    params = params.split('&')

                    for param in params:
                        # Split the parameter by '=' to separate the parameter name from the value
                        param_name, param_value = param.split('=')
                        if param_name not in param_set:
                            param_set.add(param_name)
                            fuzz_string = create_fuzz_string(20)
                            task = asyncio.ensure_future(fetch(session, base_url, param_name, fuzz_string))
                            tasks.append(task)
                    await asyncio.gather(*tasks)
                except Exception as e:
                    print(f"An error occurred while processing {url}: {e}")

    # slice the list into batches of 20
    num_batches = math.ceil(len(url_list) / batch_size)
    for i in range(0, num_batches * batch_size, batch_size):
        batch = url_list[i:i + batch_size]
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(batch))
except Exception as e:
    print(f"An error occurred: {e}")
