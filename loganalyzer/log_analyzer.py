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
from operator import attrgetter
from statistics import median
from string import Template
from typing import Dict, List, NamedTuple, Optional, Union, Generator

import yaml

LogsData = Dict[str, List[float]]


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
    date: str
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

        date = match.group(1)
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


class LogAnalys():
    """ Log analysis """

    def __init__(self, logfile: FileStat):
        self.logfile = logfile
        self.__lognumber = -1
        self.__analisis: List[ReportRaw] = []
        self.__sumrtime = -1

    def parse(self, failsborder: Optional[int] = 10) -> None:
        """ Parse logs in logfile and analyze them

        :failsborder: maximum persent of fails

        """
        logstat = self.__parse_logfile(failsborder)
        self.__analyze_stat(logstat)

    def __parse_logfile(self, failsborder: int) -> LogsData:
        """Parse logfile and return url and request time info

        :failsborder: maximum percent of fails
        :returns: Parsed logs data - url and list of request_time

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
        openfile = gzip.open if self.logfile.extention == 'gzip' else open

        linecount = 0
        faillinecount = 0
        sumrtime = 0.0
        logstat: LogsData = {}
        with openfile(self.logfile.path, 'r') as file:
            for orig_line in file:
                line = orig_line.decode('utf-8')
                linecount += 1
                result = logformat.match(line)
                if result is None:
                    faillinecount += 1
                    continue
                url, str_rtime = result.group(1, 2)
                rtime = float(str_rtime)
                if url in logstat:
                    logstat[url].append(rtime)
                else:
                    logstat[url] = [rtime]
                sumrtime += rtime

        failpersent = (faillinecount / linecount * 100 if faillinecount > 0
                       else 0)
        if failpersent > failsborder:
            raise RuntimeError('Logs has {}% not parsed lines that more than {}'
                               .format(failpersent, failsborder))
        elif failpersent > 0:
            logging.warning('Logs has {}% not parsed lines'.format(failpersent))
        self.__lognumber = linecount - faillinecount
        self.__sumrtime = sumrtime
        return logstat

    def __analyze_stat(self, logstat: LogsData) -> None:
        for url, rtimes in logstat.items():
            count_abs = len(rtimes)
            count_perc = count_abs / self.__lognumber * 100
            time_sum = sum(rtimes)
            time_avg = time_sum / count_abs
            time_max = max(rtimes)
            time_med = median(rtimes)
            time_perc = time_sum / self.__sumrtime * 100
            raw = ReportRaw(url, count_abs, count_perc, time_avg, time_max,
                            time_med, time_perc, time_sum)
            self.__analisis.append(raw)

    def report(self) -> Generator[ReportRaw, None, None]:
        """ Get parsed analysis """
        for lograw in self.__analisis:
            yield lograw


def get_report_file(logfile: FileStat, report_dir: str) -> Optional[str]:
    """ Get name of new report file

    :logfile: Stat about log file
    :report_dir: Directory with reports
    :returns: Name of new report file or None if report already exists

    """
    date = logfile.date
    report_filename = ('report-{y}.{m}.{d}.html'
                       .format(y=date[0:4], m=date[4:6], d=date[6:8]))
    report_file = os.path.join(report_dir, report_filename)
    if os.path.exists(report_file) and os.path.isfile(report_file):
        logging.info('Report {} already exist'.format(report_file))
        return None
    elif os.path.exists(report_file):
        raise RuntimeError('Report destination already exist')
    elif not os.path.exists(report_dir):
        logging.warning('Folder {} not exist'.format(report_dir))
        os.mkdir(report_dir)
        logging.info('Folder {} successfully created'.format(report_dir))
    return report_file


def put_report(analys: LogAnalys, report_file: str, report_size: int) -> None:
    """ Put report inside report_file

    :analys: log analysis
    :report_file: destination file
    :report_size: number or report lines

    """
    report = sorted(analys.report(), key=attrgetter('time_sum'),
                    reverse=True)[:report_size]
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
        loganalys = LogAnalys(last)
        loganalys.parse(config['FAILS_PERSENT'])
        put_report(loganalys, report_file, config['REPORT_SIZE'])
    except Exception as e:
        logging.exception(e)


if __name__ == "__main__":
    main()
