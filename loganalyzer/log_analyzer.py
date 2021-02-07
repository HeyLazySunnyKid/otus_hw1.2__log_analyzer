#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import os
import gzip
import logging
import sys
import re
from statistics import median
from os import listdir
from os.path import isfile, join
from typing import List, Dict, Optional, Tuple, NamedTuple, Union


Logstat = Dict[str, List[str]]
class Lograw(NamedTuple):
    url: str           # Url запроса
    count_abs: int     # сколько раз встречается URL, абсолютное значение
    count_perc: float  # сколько раз встречается URL, в процентнах относительно общего числа запросов
    time_avg: float    # средний $request_time для данного URL'а
    time_max: float    # максимальный $request_time для данного URL'а
    time_med: float    # медиана $request_time для данного URL'а
    time_perc: float   # cуммарный $request_time для данного URL'а, в процентах относительно общего $request_time всех запросов
    time_sum: float    # суммарный $request_time для данного URL'а, абсолютное значение

class Filestat(NamedTuple):
    path: str
    data: str
    extention: str


config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "FAILS_PERSENT": 10
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

class LogAnalys():
    loganalys: Tuple[Lograw]

    def __init__(self, logfile: Filestat):
        self.logfile = logfile
        self.__lognumber = -1
        self.__analys = []
        self.__sumrtime = -1

    def parse(self, fails: Optional[int] = 10):
        logstat = self.__parse_logfile(fails)
        self.__analyze_stat(logstat)
        pass

    def __parse_logfile(self, fails: int) -> Logstat:
        """TODO: Docstring for parse_logfile.

        :arg1: TODO
        :returns: TODO

        """
        logformat = r'\s+'.join([
            r'\S+',                 # $remote_addr
            r'\S+',                 # $remote_user
            r'\S+',                 # $http_x_real_ip
            r'\[[^\]]+\]',          # [$time_local]
            r'"\w+\s+(\S+)[^"]*"',  # "$request", group(1)
            r'\S+',                 # $status
            r'\S+',                 # $body_bytes_sent
            r'"[^"]+"',             # "$http_referer"
            r'"[^"]+"',             # "$http_user_agent"
            r'"[^"]+"',             # "$http_x_forwarded_for"
            r'"[^"]+"',             # "$http_X_REQUEST_ID"
            r'"[^"]+"',             # "$http_X_RB_USER"
            r'(\S+)'                # $request_time, group(2)
        ])
        logformat = re.compile(logformat)
        openfile = gzip.open if self.logfile.extention == 'gzip' else open

        linecount = 0
        faillinecount = 0
        sumrtime = 0
        logstat = {}
        with openfile(self.logfile.path, 'r') as file:
            for orig_line in file:
                line = orig_line.decode('utf-8')
                linecount += 1
                result = logformat.match(line)
                if result is None:
                    faillinecount += 1
                    print('failed line:', line)
                    continue
                url, rtime = result.group(1, 2)
                rtime = float(rtime)
                if url in logstat:
                    logstat[url].append(rtime)
                else:
                    logstat[url] = [rtime]
                sumrtime += rtime

                # debug
                if linecount == 100:
                    break
        if faillinecount > 0 and (faillinecount / faillinecount * 100) > fails:
            raise RuntimeError('Nubmer of fails more than limit')
        self.__lognumber = linecount - faillinecount
        self.__sumrtime = sumrtime
        return logstat

    def __analyze_stat(self, logstat: Logstat) -> None:
        for url, rtimes in logstat.items():
            count_abs = len(rtimes)
            count_perc = count_abs / self.__lognumber * 100
            time_sum = sum(rtimes)
            time_avg = time_sum / count_abs
            time_max = max(rtimes)
            time_med = median(rtimes)
            time_perc = time_sum / self.__sumrtime * 100
            raw = Lograw(url, count_abs, count_perc, time_avg, time_max, 
                         time_med, time_perc, time_sum)
            self.__analys.append(Lograw)

    def report(self) -> Lograw:
        for lograw in self.__analys:
            yield lograw


def view(logs: Lograw):
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
