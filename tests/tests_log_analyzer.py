import unittest
from unittest.mock import patch
import loganalyzer.log_analyzer as la


class TestLogAnylyzer(unittest.TestCase):

    def setUp(self):
        self.general_filenames = [
            'nginx-access-ui.log-20190629.gz',
            'nginx-access-ui.log-20190630.gz',
            'nginx-access-ui.log-20190629',
            'apache-access-ui.log-20190631.gz'
        ]


    def test_get_latets_logfile_gzip(self):
        with patch('loganalyzer.log_analyzer.listdir',
                   return_value=self.general_filenames):
            path, data, extention = la.get_latest_logfile('./test_directory')

        self.assertEqual(path, './test_directory/nginx-access-ui.log-20190630.gz')
        self.assertEqual(data, '20190630')
        self.assertEqual(extention, 'gzip')

    def test_get_latest_logfile_plain(self):
        self.general_filenames.append('nginx-access-ui.log-20190631')
        with patch('loganalyzer.log_analyzer.listdir',
                   return_value=self.general_filenames):
            path, data, extention = la.get_latest_logfile('./test_directory')
        self.assertEqual(path, './test_directory/nginx-access-ui.log-20190631')
        self.assertEqual(data, '20190631')
        self.assertEqual(extention, 'plain')

    def test_get_latest_logfile_none(self):
        filesnames = [
            'apache-access-ui.log-20190631.gz',
            'postgresql-access-ui.log-20190631'
        ]
        with patch('loganalyzer.log_analyzer.listdir',
                   return_value=filesnames):
            self.assertIsNone(la.get_latest_logfile('./test_directory'))
