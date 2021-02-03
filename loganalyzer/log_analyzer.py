#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import logging
import sys
from collections import namedtuple
from os import listdir
from os.path import isfile, join
from typing import NamedTuple

Lograw = NamedTuple('Lograw', [
    ['url', str],           # Url запроса
    ['count', int],         # сколько раз встречается URL, абсолютное значение
    ['count_perc', float],  # сколько раз встречается URL, в процентнах относительно общего числа запросов
    ['time_avg', float],    # средний $request_time для данного URL'а
    ['time_max', float],    # максимальный $request_time для данного URL'а
    ['time_med', float],    # медиана $request_time для данного URL'а
    ['time_perc', float],   # сколько раз встречается URL, в процентнах относительно общего числа запросов
    ['time_sum', float]     # суммарный $request_time для данного URL'а, абсолютное значение
])

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

def get_latest_logfile(logdir: str) -> (str, str):
    """TODO: Docstring for get_latest_logfile.

    :logdir: TODO
    :returns: TODO

    """
    pass


def parse_logfile(log) -> List[Lograw]:
    """TODO: Docstring for parse_logfile.

    :arg1: TODO
    :returns: TODO

    """
    pass


def load_config(configfile=None: str) -> dict:
    """TODO: Load configuration and validate it

    :configfile: Configuration file (if defined)
    :returns: Actual config

    """
    pass

def main():
    pass

if __name__ == "__main__":
    main()
