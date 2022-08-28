import argparse
import os
import re
import time

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# https://stackoverflow.com/a/14117511/3190077
def check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return ivalue


parser = argparse.ArgumentParser(
    description="Load new matches across all wants of a vialibri account"
)
parser.add_argument("-o", "--offset", type=check_positive, default=1)
parser.add_argument("-l", "--limit", type=check_positive)


class Session(object):
    _host = "https://www.vialibri.net"
    _user_agent = {
        "User-Agent": os.environ.get("USER_AGENT"),
    }
    _wants_url = _host + "/wants"
    _api_calls_time_interval = int(os.environ.get("API_CALLS_TIME_INTERVAL"))

    def __init__(self, session):
        self.session = session
        self.session.headers.update(self._user_agent)

    def __enter__(self):
        login_url = self._host + "/account/login"
        login_page = BeautifulSoup(
            self.session.get(login_url).content,
            "html.parser",
        )
        csrf_token = login_page.body.find("input", {"name": "csrf-token"}).get("value")
        data = {
            "csrf-token": csrf_token,
            "return-to": False,
            "username": os.environ.get("USERNAME"),
            "password": os.environ.get("PASSWORD"),
        }
        self.session.post(login_url, json=data)
        return self

    def __exit__(self, type, value, traceback):
        logout_url = self._host + "/account/logout"
        self.session.get(logout_url)

    def get_wants_ids(self):
        wants_page = self.session.get(self._wants_url).content.decode("utf-8")
        wants_ids = re.findall(r"(?<=\"id\":)\d+", wants_page)
        return wants_ids

    def load_wants(self, offset, limit):
        start = offset - 1
        stop = start + limit if limit else None
        wants_ids = self.get_wants_ids()[start:stop]

        for index, id in enumerate(wants_ids):
            time.sleep(self._api_calls_time_interval)
            want_url = f"{self._wants_url}/{id}/search?include=new"
            print(f"{offset + index}: {want_url}")
            self.session.get(want_url)


if __name__ == "__main__":
    args = parser.parse_args()
    offset = args.offset
    limit = args.limit

    with requests.Session() as s, Session(s) as session:
        session.load_wants(offset, limit)
