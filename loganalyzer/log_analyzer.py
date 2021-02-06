#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import logging
import sys
import re
from os import listdir
from os.path import isfile, join
from typing import Dict, Optional, Tuple, NamedTuple, Union


class Lograw(NamedTuple):
    url: str           # Url запроса
    count_abs: int     # сколько раз встречается URL, абсолютное значение
    count_perc: float  # сколько раз встречается URL, в процентнах относительно общего числа запросов
    time_avg: float    # средний $request_time для данного URL'а
    time_max: float    # максимальный $request_time для данного URL'а
    time_med: float    # медиана $request_time для данного URL'а
    time_perc: float   # сколько раз встречается URL, в процентнах относительно общего числа запросов
    time_sum: float    # суммарный $request_time для данного URL'а, абсолютное значение

class Filestat(NamedTuple):
    path: str
    data: str
    extention: str


config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def get_latest_logfile(logdir: str) -> Optional[Filestat]:
    """ Return info about latest log inside logdir

    :logdir: path to logdir
    :returns: None if logfile not found or Filestat about latest file

    """

    # TODO: move file start to config
    parser = re.compile(r'nginx-access-ui.log-(\d+).?(\w*)')
    last = None
    for file in listdir(logdir):
        match = parser.match(file)
        if match is None:
            continue

        data = match.group(1)
        if match.group(2) in ['', 'log', 'txt']:
            extention = 'plain'
        elif match.group(2) in ['gz', 'gzip']:
            extention = 'gzip'
        else:
            continue
        if last is None or data > last.data:
            last = Filestat(join(logdir, match.group(0)),
                            data, extention)
    return last


def parse_logfile(logfile: str) -> Tuple[Lograw]:
    """TODO: Docstring for parse_logfile.

    :arg1: TODO
    :returns: TODO

    """
    pass


def load_config(configfile: Optional[str] = None) -> Dict[str, Union[str, int]]:
    """TODO: Load configuration and validate it

    :configfile: Configuration file (if defined)
    :returns: Actual config

    """
    pass


def main() -> None:
    pass


if __name__ == "__main__":
    main()
