#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sqlite3
import typing
import getpass
import datetime
import re
import subprocess
import xml.dom.minidom  # type: ignore
import sys

ACCOUNTING_ITEMS = [
    ("qname", "TEXT"),
    ("hostname", "TEXT"),
    ("group", "TEXT"),
    ("owner", "TEXT"),
    ("job_name", "TEXT"),
    ("job_number", "INTEGER"),
    ("account", "TEXT"),
    ("priority", "TEXT"),
    ("submission_time", "INTEGER"),
    ("start_time", "INTEGER"),
    ("end_time", "INTEGER"),
    ("failed", "INTEGER"),
    ("exit_status", "INTEGER"),
    ("ru_wallclock", "REAL"),
    ("ru_utime", "REAL"),
    ("ru_stime", "REAL"),
    ("ru_maxrss", "REAL"),
    ("ru_ixrss", "REAL"),
    ("ru_ismrss", "REAL"),
    ("ru_idrss", "REAL"),
    ("ru_isrss", "REAL"),
    ("ru_minflt", "REAL"),
    ("ru_majflt", "REAL"),
    ("ru_nswap", "REAL"),
    ("ru_inblock", "REAL"),
    ("ru_oublock", "REAL"),
    ("ru_msgsnd", "REAL"),
    ("ru_msgrcv", "REAL"),
    ("ru_nsignals", "REAL"),
    ("ru_nvcsw", "REAL"),
    ("ru_nivcsw", "REAL"),
    ("project", "TEXT"),
    ("department", "TEXT"),
    ("granted_pe", "TEXT"),
    ("slots", "INTEGER"),
    ("task_number", "INTEGER"),
    ("cpu", "REAL"),
    ("mem", "REAL"),
    ("io", "REAL"),
    ("category", "TEXT"),
    ("iow", "REAL"),
    ("pe_taskid", "TEXT"),
    ("maxvmem", "TEXT"),
    ("arid", "TEXT"),
    ("ar_submission_time", "TEXT"),
    ("job_class", "TEXT"),
    ("qdel_info", "TEXT"),
    ("maxrss", "TEXT"),
    ("maxpass", "TEXT"),
    ("submit_host", "TEXT"),
    ("cwd", "TEXT"),
    ("submit_cmd", "TEXT"),
    ("wallclock", "REAL"),
    ("ioops", "REAL"),
    ("bound_cores", "INTEGER"),
]


def _main():
    parser = argparse.ArgumentParser(description="UGE Accounting Loader")
    parser.add_argument('--database',
                        default=get_default_database_path(),
                        help='default: %(default)s')
    parser.add_argument('--accounting',
                        default=os.path.join(os.environ['SGE_ROOT'],
                                             os.environ['SGE_CELL'],
                                             'common/accounting'),
                        help='default: %(default)s',
                        type=argparse.FileType('r',
                                               encoding='utf-8',
                                               errors='ignore'))
    options = parser.parse_args()

    db = connect_database(options.database)
    load_data(db, options.accounting)

    for one in get_recent_data(db, days=7, hours=0):
        cpu_time = one['ru_utime'] + one['ru_stime']
        wallclock = one['ru_wallclock']
        expected_cpu_time = wallclock * one['slots']
        cpu_efficiency = cpu_time / expected_cpu_time
        memory_efficiency = int(
            one['maxvmem']) / (get_mem_req(one['category']) * one['slots'])

        print(
            one['job_number'], one['job_name'], one['slots'],
            human_memory_display(get_mem_req(one['category']) * one['slots']),
            human_memory_display(int(one['maxvmem'])),
            '{:.3f}'.format(memory_efficiency),
            '{:.3f}'.format(cpu_efficiency))


def get_default_database_path() -> str:
    return os.path.expanduser('~/.local/var/grid/accounting.sqlite3')


def connect_database(dbpath: str) -> sqlite3.Connection:
    if not os.path.isdir(os.path.dirname(dbpath)):
        os.makedirs(os.path.dirname(dbpath))

    db = sqlite3.connect(dbpath)
    db.row_factory = sqlite3.Row
    return db


MEM_REQ = re.compile(r'mem_req=([\d.]+)([GMk]?)')


def get_mem_req(category: str) -> int:
    matches = MEM_REQ.search(category)
    if not matches:
        return 4 * 1024 * 1024 * 1024
    suffix = matches.group(2)
    value = float(matches.group(1))
    if suffix == 'k':
        return int(value * 1024)
    if suffix == 'M':
        return int(value * 1024 * 1024)
    if suffix == 'G':
        return int(value * 1024 * 1024 * 1024)
    if suffix == '':
        return int(value)
    raise Exception('invalid mem_req: {}'.format(category))


S_VMEM = re.compile(r's_vmem=([\d.]+)([GMk]?)')


def get_svmem(category: str) -> int:
    matches = S_VMEM.search(category)
    if not matches:
        return 4 * 1024 * 1024 * 1024
    suffix = matches.group(2)
    value = float(matches.group(1))
    if suffix == 'k':
        return int(value * 1024)
    if suffix == 'M':
        return int(value * 1024 * 1024)
    if suffix == 'G':
        return int(value * 1024 * 1024 * 1024)
    if suffix == '':
        return int(value)
    raise Exception('invalid mem_req: {}'.format(category))


def human_memory_display(mem: int) -> str:
    if mem > 1024 * 1024 * 1024:
        return "{:.2f}G".format(mem / (1024 * 1024 * 1024))
    if mem > 1024 * 1024:
        return "{:.2f}M".format(mem / (1024 * 1024))
    if mem > 1024:
        return "{:.2f}k".format(mem / (1024))
    return str(mem)


def get_recent_data(db: sqlite3.Connection,
                    owner: str = None,
                    days: int = 7,
                    hours: int = 0,
                    succeeded_only: bool = False,
                    failed_only: bool = False) -> typing.Iterator[sqlite3.Row]:
    if not owner:
        owner = getpass.getuser()

    begin_date = datetime.datetime.now() - datetime.timedelta(days=days,
                                                              hours=hours)

    if owner == '*':
        sql = (
            'SELECT * FROM accounting WHERE end_time > ? {} ' +
            'ORDER BY job_number, task_number'
        ).format('AND failed = 0 AND exit_status = 0' if succeeded_only else (
            'AND (failed <> 0 OR exit_status <> 0)' if failed_only else ''))
        cur = db.execute(sql, (begin_date.timestamp() * 1000, ))
    else:
        sql = (
            'SELECT * FROM accounting WHERE end_time > ? AND owner = ?' +
            ' {} ORDER BY job_number, task_number'
        ).format('AND failed = 0 AND exit_status = 0' if succeeded_only else (
            'AND (failed <> 0 OR exit_status <> 0)' if failed_only else ''))
        cur = db.execute(sql, (begin_date.timestamp() * 1000, owner))
    return cur


def add_info_to_record(one: dict) -> dict:
    one['cpu_time'] = one['ru_utime'] + one['ru_stime']
    wallclock = one['ru_wallclock']
    one['expected_cpu_time'] = wallclock * one['slots']
    if one['expected_cpu_time'] > 0:
        one['cpu_use%'] = one['cpu_time'] / one['expected_cpu_time'] * 100
    else:
        one['cpu_use%'] = 100.0
    one['mem_req'] = get_mem_req(one['category'])
    one['total_mem_req'] = one['mem_req'] * one['slots']
    one['s_vmem'] = get_svmem(one['category'])
    one['total_s_vmem'] = one['s_vmem'] * one['slots']
    one['memory_use%'] = int(
        one['maxvmem']) / (one['mem_req'] * one['slots']) * 100

    job_id = str(one['job_number'])
    if one['task_number'] > 0:
        job_id += "." + str(one['task_number'])
    one['job_id'] = job_id

    return one


def load_data(db: sqlite3.Connection, accounting: typing.TextIO):
    db.execute('CREATE TABLE IF NOT EXISTS accounting(' +
               ','.join(['"{}" {}'.format(*x)
                         for x in ACCOUNTING_ITEMS]) + ')')
    db.execute(
        'CREATE TABLE IF NOT EXISTS processed_bytes(processed_bytes INTEGER)')

    count = 0

    data = [
        x for x in db.execute('SELECT processed_bytes FROM processed_bytes')
    ]
    if data:
        accounting.seek(data[0][0])

    while True:
        line = accounting.readline()
        if not line:
            break
        if line[0] == '#':
            continue
        row = line.strip().split(':')
        row_data = {x[0]: y for (x, y) in zip(ACCOUNTING_ITEMS, row)}
        db.execute(
            'INSERT INTO accounting(' +
            ','.join(['"{}"'.format(x) for x in row_data]) + ') VALUES (' +
            ','.join(['?' for x in row_data]) + ')',
            [x for x in row_data.values()])

        count += 1
        if (count % 10000) == 0:
            print("Processing {} entries".format(count), file=sys.stderr)

    db.execute('DELETE from processed_bytes')
    db.execute('INSERT INTO processed_bytes(processed_bytes) VALUES(?)',
               [accounting.tell()])

    for one in [
            'owner', 'job_number', 'submission_time', 'start_time', 'end_time'
    ]:
        db.execute(
            'CREATE INDEX IF NOT EXISTS accounting__{0} ON accounting({0})'.
            format(one))

    db.commit()


def qstat(args=[]):
    result = subprocess.run(['qstat', '-xml', '-u', '*', '-r'],
                            capture_output=True,
                            check=True)
    dom = xml.dom.minidom.parseString(result.stdout)

    job_elements = dom.getElementsByTagName('job_list')
    jobs = []
    for one_job in job_elements:
        new_one = {
            'name':
            one_job.getElementsByTagName('JB_name')[0].firstChild.data.strip(),
            'job_id':
            one_job.getElementsByTagName(
                'JB_job_number')[0].firstChild.data.strip(),
            'owner':
            one_job.getElementsByTagName(
                'JB_owner')[0].firstChild.data.strip(),
            'state':
            one_job.getElementsByTagName('state')[0].firstChild.data.strip(),
            'slots':
            one_job.getElementsByTagName('slots')[0].firstChild.data.strip(),
            'priority':
            one_job.getElementsByTagName('JAT_prio')
            [0].firstChild.data.strip(),
        }

        if one_job.getElementsByTagName(
                'queue_name') and one_job.getElementsByTagName(
                    'queue_name')[0].firstChild:
            new_one['queue_name'] = one_job.getElementsByTagName(
                'queue_name')[0].firstChild.data.strip()
        if one_job.getElementsByTagName(
                'tasks') and one_job.getElementsByTagName(
                    'tasks')[0].firstChild:
            new_one['tasks'] = one_job.getElementsByTagName(
                'tasks')[0].firstChild.data.strip()
        if one_job.getElementsByTagName(
                'JAT_start_time') and one_job.getElementsByTagName(
                    'JAT_start_time')[0].firstChild:
            new_one['start_time'] = datetime.datetime.strptime(
                one_job.getElementsByTagName('JAT_start_time')
                [0].firstChild.data.strip(), '%Y-%m-%dT%H:%M:%S.%f')
        if one_job.getElementsByTagName(
                'JB_submission_time') and one_job.getElementsByTagName(
                    'JB_submission_time')[0].firstChild:
            new_one['submission_time'] = datetime.datetime.strptime(
                one_job.getElementsByTagName('JB_submission_time')
                [0].firstChild.data.strip(), '%Y-%m-%dT%H:%M:%S.%f')

        jobs.append(new_one)
    return jobs


if __name__ == '__main__':
    _main()
