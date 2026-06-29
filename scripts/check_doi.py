import asyncio
import csv
import datetime
from concurrent.futures import ThreadPoolExecutor
import os
import sys
import sqlmodel
import urllib.request
import urllib.error
import http
import http.client

# Get the parent directory and add it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


from src._common.models import DOI
from src._common.constants import DB_URL


db_engine = sqlmodel.create_engine(DB_URL)


ASLUG = "migration-and-HERitage"
MAX_CONCURRENT_REQUESTS = 5
REQUEST_TIMEOUT = 25  # seconds


urls_to_check = []
responses = {}
headers = {"From": "tnb.admin@uni.lu"}


if __name__ == "__main__":
    with sqlmodel.Session(db_engine) as session:
        stmt = sqlmodel.select(DOI).where(DOI.slug == ASLUG)
        results = session.exec(stmt)
        dois = results.all()

    for doi in dois:
        if doi.proxy is None:
            url = f"https://doi.org/{doi.doi}"
            urls_to_check.append(url)
        else:
            raise NotImplementedError

    def sync_fetch(url: str, timeout: int):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.getcode()
        except urllib.error.HTTPError as he:
            return he.code
        except Exception as exc:
            return f"error: {exc!r}"

    async def fetch(url: str, sem: asyncio.Semaphore, executor: ThreadPoolExecutor):
        loop = asyncio.get_running_loop()
        await sem.acquire()
        try:
            status = await loop.run_in_executor(
                executor, sync_fetch, url, REQUEST_TIMEOUT
            )
            responses[url] = http.client.responses.get(status, status)
        finally:
            sem.release()

    async def main(urls):
        sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        # Keep executor workers bounded to avoid using all resources
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
            tasks = [asyncio.create_task(fetch(u, sem, executor)) for u in urls]
            await asyncio.gather(*tasks)

    # Spawn tasks that call blocking urllib.request.urlopen in a bounded thread pool
    asyncio.run(main(urls_to_check))

    for u, s in responses.items():
        print(u, s)

    with open(
        f"dois_{ASLUG}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "w",
        newline="",
    ) as f:
        w = csv.writer(f)
        w.writerow(["url", "status"])
        for url, status in responses.items():
            w.writerow([url, status])
