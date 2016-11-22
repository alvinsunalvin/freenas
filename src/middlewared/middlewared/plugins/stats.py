from middlewared.schema import Str, accepts
from middlewared.service import Service
from middlewared.utils import Popen

import glob
import os
import re
import subprocess


RRD_PATH = '/var/db/collectd/rrd/localhost/'

RE_DSTYPE = re.compile(r'ds\[(\w+)\]\.type = "(\w+)"')
RE_STEP = re.compile(r'step = (\d+)')
RE_LAST_UPDATE = re.compile(r'last_update = (\d+)')


class StatsService(Service):

    @accepts()
    def get_sources(self):
        """
        Returns an object with all available sources tried with metric datasets.
        """
        sources = {}
        if not os.path.exists(RRD_PATH):
            return {}
        for i in glob.glob('{}/*/*.rrd'.format(RRD_PATH)):
            source, metric = i.replace(RRD_PATH, '').split('/', 1)
            if metric.endswith('.rrd'):
                metric = metric[:-4]
            if source not in sources:
                sources[source] = []
            sources[source].append(metric)
        return sources

    @accepts(Str('source'), Str('name'))
    def get_dataset_info(self, source, name):
        """
        Returns info about a given dataset from some source.
        """
        rrdfile = '{}/{}/{}.rrd'.format(RRD_PATH, source, name)
        proc = Popen(
            ["rrdtool", "info", rrdfile],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        data, err = proc.communicate()
        if proc.returncode != 0:
            raise ValueError('rrdtool failed: {}'.format(err))

        info = {
            'data_sources': {}
        }
        for data_source, _type in RE_DSTYPE.findall(data):
            info['data_sources'][data_source] = {'type': _type}

        reg = RE_STEP.search(data)
        if reg:
            info['step'] = int(reg.group(1))
        reg = RE_LAST_UPDATE.search(data)
        if reg:
            info['last_update'] = int(reg.group(1))
        return info
