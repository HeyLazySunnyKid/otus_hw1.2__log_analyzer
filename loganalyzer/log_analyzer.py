#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: log_analyzer.py
Author: HeyLazySunnyKid
Email: denis.kaluzhnyy@gmail.com
Github: https://github.com/HeyLazySunnyKid/otus_hw1.2__log_analyzer
Description: Otus homework. Script for analyze logs.
"""


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import argparse
import gzip
import json
import logging
import os
import re
import sys
import datetime
from operator import attrgetter
from statistics import median
from string import Template
from typing import Iterable, Dict, Tuple, List, NamedTuple, Optional, Union, Generator

import yaml

LogsData = Dict[str, List[float]]


class ParseStat(NamedTuple):
    """ File parse lines statistic """
    count: int
    success: int
    fail: int


class ReportRaw(NamedTuple):
    """ Raw of report """
    url: str           # Url запроса
    count: int         # сколько раз встречается URL, абсолютное значение
    count_perc: float  # сколько раз встречается URL, в процентнах относительно общего числа запросов
    time_avg: float    # средний $request_time для данного URL'а
    time_max: float    # максимальный $request_time для данного URL'а
    time_med: float    # медиана $request_time для данного URL'а
    time_perc: float   # cуммарный $request_time для данного URL'а, в процентах относительно общего $request_time всех запросов
    time_sum: float    # суммарный $request_time для данного URL'а, абсолютное значение


class FileStat(NamedTuple):
    """ Stat about file """
    path: str
    date: datetime.datetime
    extention: str


global_config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "FAILS_PERSENT": 80
}


def get_latest_logfile(logdir: str) -> Optional[FileStat]:
    """ Return stat about latest log inside logdir

    :logdir: path to logdir
    :returns: None if log file not found or latest file's FileStat

    """
    parser = re.compile(r'nginx-access-ui.log-(\d+).?(\w*)')
    last = None
    for file in os.listdir(logdir):
        match = parser.match(file)
        if match is None:
            continue

        date = datetime.datetime.strptime(match.group(1), '%Y%m%d')
        if match.group(2) in ['', 'log', 'txt']:
            extention = 'plain'
        elif match.group(2) in ['gz', 'gzip']:
            extention = 'gzip'
        else:
            continue
        if last is None or date > last.date:
            last = FileStat(os.path.join(logdir, match.group(0)),
                            date, extention)
    return last


def parse_url_request_time(logfile: FileStat) -> Tuple[LogsData, ParseStat]:
    """Parse logfile and return url with list of request_time

    :logfile: Information about log's file
    :returns: Parsed logs data - url and list of request_time
                Parse statistic - number of failes and successes
    """
    re_logformat = r'\s+'.join([
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
    logformat = re.compile(re_logformat)
    openfile = gzip.open if logfile.extention == 'gzip' else open

    success = 0
    fail = 0
    logstat: LogsData = {}
    with openfile(logfile.path, 'r') as file:
        for orig_line in file:
            line = orig_line.decode('utf-8')
            result = logformat.match(line)
            if result is None:
                fail += 1
                continue
            success += 1
            url, str_rtime = result.group(1, 2)
            rtime = float(str_rtime)
            if url in logstat:
                logstat[url].append(rtime)
            else:
                logstat[url] = [rtime]

    parsestat = ParseStat(success+fail, success, fail)
    return logstat, parsestat


def check_fails(parsestat: ParseStat, failsborder: int = 10) -> None:
    """ Check number of failes

    :parsestat: Parse statistic

    """
    failpersent = (
        parsestat.fail / parsestat.count * 100 if parsestat.fail > 0 else 0
    )
    if failpersent > failsborder:
        raise RuntimeError('Logs has {}% not parsed lines that more than {}'
                           .format(failpersent, failsborder))
    elif failpersent > 0:
        logging.warning('Logs has {}% not parsed lines'.format(failpersent))


def get_report(logstat: LogsData, parsestat: ParseStat) -> Generator[ReportRaw, None, None]:
    """ Generator of report raws

    :logstat: Staticstic of url in logs
    :parsestat: Parse statistic
    :returns: Raws of analysis report

    """
    sumrtime = sum((sum(v) for k, v in logstat.items()))
    for url, rtimes in logstat.items():
        count_abs = len(rtimes)
        count_perc = count_abs / parsestat.count * 100
        time_sum = sum(rtimes)
        time_avg = time_sum / count_abs
        time_max = max(rtimes)
        time_med = median(rtimes)
        time_perc = time_sum / sumrtime * 100
        raw = ReportRaw(url, count_abs, count_perc, time_avg, time_max,
                        time_med, time_perc, time_sum)
        yield raw


def get_report_file(logfile: FileStat, report_dir: str) -> Optional[str]:
    """ Get name of new report file

    :logfile: Stat about log file
    :report_dir: Directory with reports
    :returns: Name of new report file or None if report already exists

    """
    date = logfile.date
    report_filename = date.strftime('report-%Y.%m.%d.html')
    report_file = os.path.join(report_dir, report_filename)
    if os.path.exists(report_file) and os.path.isfile(report_file):
        logging.info('Report {} already exist'.format(report_file))
        return None
    return report_file


def put_report(stat: Iterable[ReportRaw], report_file: str, report_size: int) -> None:
    """ Put report inside report_file

    :analys: log analysis
    :report_file: destination file
    :report_size: number or report lines

    """
    report = sorted(stat, key=attrgetter('time_sum'), reverse=True)[:report_size]
    table_json = json.dumps([raw._asdict() for raw in report])

    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'resources', 'report.html')
    with open(template_path, 'r') as file:
        template = Template(file.read())
    report_html = template.safe_substitute(table_json=table_json)

    with open(report_file, 'w') as file:
        file.write(report_html)
    logging.info('Report {} successfully created'.format(report_file))


def load_config(config: Dict[str, Union[str, int]]) -> Dict[str, Union[str, int]]:
    """Load configuration using config file and default

    :config: Default configuration
    :returns: Actual configuration

    """
    # TODO: argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='config file path')
    args = parser.parse_args()
    config_path = 'config.yaml' if args.config is None else args.config
    with open(config_path, 'r') as file:
        file_config = yaml.load(file, Loader=yaml.FullLoader)
    config.update(file_config)
    return config


def main() -> None:
    try:
        config = load_config(dict(global_config))
        logging.basicConfig(filename=config.get('LOGFILE'),
                            level=logging.DEBUG,
                            format='[%(asctime)s] %(levelname).1s %(message)s',
                            datefmt='%Y.%m.%d %H:%M:%S')
        logging.info('Initialization completed')
        last = get_latest_logfile(config['LOG_DIR'])
        report_file = get_report_file(last, config['REPORT_DIR'])
        if report_file is None:
            sys.exit(0)
        urlstat, parsestat = parse_url_request_time(last)
        check_fails(parsestat)
        stat = get_report(urlstat, parsestat)
        put_report(stat, report_file, config['REPORT_SIZE'])
    except Exception as e:
        logging.exception(e)


if __name__ == "__main__":
    main()
