#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os.path
import sys
import collections
import getpass
import datetime
import os
import cromwellhelper.pager as pager
import cromwellhelper.printtable as printtable
import cromwellhelper.uge as uge


def _main():
    try:
        __main()
    except BrokenPipeError:
        # ignore broken pipe
        pass


def __main():
    parser = argparse.ArgumentParser(description="Grid Engine Helper")
    parser.add_argument('--database',
                        default=os.path.expanduser("~/.grid.sqlite3"),
                        help='Cache database (default: %(default)s)')
    parser.add_argument('--no-pager',
                        action='store_true',
                        help='Do not use pager')
    subparsers = parser.add_subparsers(required=True)

    stat_parser = subparsers.add_parser(
        'stat', help='Show status of running and pending jobs')
    stat_parser.set_defaults(func=stat)
    stat_parser.add_argument('--user',
                             '-u',
                             help='User name (default: %(default)s)',
                             default=getpass.getuser())

    tablist_parser = subparsers.add_parser(
        'tablist', help='Tab separated list of running and pending jobs')
    tablist_parser.set_defaults(func=tablist)
    tablist_parser.add_argument('--user',
                                '-u',
                                help='User name (default: %(default)s)',
                                default=getpass.getuser())
    tablist_parser.add_argument('--state',
                                '-s',
                                help='State (default: %(default)s)',
                                default='*')

    record_parser = subparsers.add_parser(
        'records', help='Show recent finished job records')
    record_parser.set_defaults(func=records)
    record_parser.add_argument('--user',
                               '-u',
                               help='User name (default: %(default)s)',
                               default=getpass.getuser())
    record_parser.add_argument('--tab-table', action='store_true')
    record_parser.add_argument('--database',
                               help='Database path (default: %(default)s)',
                               default=uge.get_default_database_path())
    record_parser.add_argument('--days',
                               help='Days (default: %(default)s)',
                               default=7,
                               type=int)
    record_parser.add_argument('--hours',
                               help='Days (default: %(default)s)',
                               default=0,
                               type=int)
    record_parser.add_argument('--succeeded-only', action='store_true')
    record_parser.add_argument('--failed-only', action='store_true')

    show_parser = subparsers.add_parser('show', help='Show job detail')
    show_parser.set_defaults(func=detail)
    show_parser.add_argument('--database',
                             help='Database path (default: %(default)s)',
                             default=uge.get_default_database_path())
    show_parser.add_argument('job_id', help='Job ID')

    if len(sys.argv) == 1:
        print("subcommand is required", file=sys.stderr)
        parser.print_help()
        return

    options = parser.parse_args()

    pager.AutoPager(options.no_pager)
    options.func(options)


def duration(d: datetime.timedelta) -> str:
    s = ''
    if d.days > 0:
        s += '{}d '.format(d.days)
    sec = d.seconds
    if sec > 60 * 60:
        s += '{}h '.format(int(sec / (60 * 60)))
        sec = sec % (60 * 60)
    if sec > 60:
        s += '{}m '.format(int(sec / (60)))
        sec = sec % 60
    s += '{}.{:03d}s'.format(int(sec), int(d.microseconds / 1000))
    return s


def detail(options):
    db = uge.connect_database(options.database)
    with open(os.path.join(os.environ['SGE_ROOT'], os.environ['SGE_CELL'],
                           'common/accounting'),
              errors='ignore') as f:
        uge.load_data(db, f)

    job_id = options.job_id.split('.')
    if len(job_id) == 1:
        job_number = int(job_id[0])
        cur = db.execute('SELECT * FROM accounting WHERE job_number = ?',
                         (job_number, ))
    elif len(job_id) == 2:
        (job_number, task_number) = [int(x) for x in job_id]
        cur = db.execute(
            'SELECT * FROM accounting WHERE job_number = ?' +
            ' AND task_number = ?', (job_number, task_number))
    else:
        raise Exception('Invalid job ID: {}'.format(options.job_id))

    for one in cur:
        one = uge.add_info_to_record(dict(one))

        for k, v in dict(one).items():
            if k == 'submission_time' or k == 'start_time' or k == 'end_time':
                d = datetime.datetime.fromtimestamp(v / 1000)
                v = d.strftime('%Y/%m/%d %H:%M:%S')
            elif k in {
                    'maxvmem', 'mem', 'total_mem_req', 'mem_req', 's_vmem',
                    'total_s_vmem'
            }:
                v = uge.human_memory_display(int(v))
            elif k in {
                    'wallclock', 'ru_utime', 'ru_stime', 'ru_wallclock',
                    'cpu_time', 'expected_cpu_time'
            }:
                v = duration(datetime.timedelta(seconds=v))
            elif k in {'memory_use%', 'cpu_use%'}:
                v = '{:.1f}%'.format(v)
            print('{:>18} : {}'.format(k, v))

        print('-----------------')


def check_bad_parameters(options):
    db = uge.connect_database(options.database)
    with open(os.path.join(os.environ['SGE_ROOT'], os.environ['SGE_CELL'],
                           'common/accounting'),
              errors='ignore') as f:
        uge.load_data(db, f)
    data = uge.get_recent_data(db,
                               owner=options.user,
                               days=options.days,
                               hours=options.hours,
                               succeeded_only=options.succeeded_only,
                               failed_only=options.failed_only)

    if options.tab_table:
        table = printtable.TabTable()
    else:
        table = printtable.PrettyTable()
        table.add_row('queue', 'owner', 'hostname', 'job number',
                      'task number', 'job name', 'slots', 'wallclock',
                      'submission', 'mem req', 's_vmem', 'maxvmem',
                      'mem used%', 'cpu used%', 'reason')

    for one in data:
        cpu_time = one['ru_utime'] + one['ru_stime']
        wallclock = one['ru_wallclock']
        wallclock_delta = datetime.timedelta(seconds=wallclock)
        expected_cpu_time = wallclock * one['slots']
        cpu_efficiency = cpu_time / expected_cpu_time
        mem_req = uge.get_mem_req(one['category'])
        s_vmem = uge.get_svmem(one['category'])
        memory_efficiency = int(
            one['maxvmem']) / (uge.get_mem_req(one['category']) * one['slots'])

        reason = []

        if cpu_efficiency > 1.5:
            reason.append('more slots required')
        if memory_efficiency > 1.5:
            reason.append('more memory required')
        if mem_req != s_vmem:
            reason.append('mem_req parameter is not equal to s_vmem')

        if reason:
            table.add_row(
                one['qname'], one['owner'], one['hostname'], one['job_number'],
                one['task_number'], one['job_name'], one['slots'],
                duration(wallclock_delta),
                datetime.datetime.fromtimestamp(
                    one['submission_time'] /
                    1000).strftime('%Y/%m/%d %H:%M:%S'),
                uge.human_memory_display(mem_req),
                uge.human_memory_display(s_vmem),
                uge.human_memory_display(int(one['maxvmem'])),
                '{:.3f}'.format(memory_efficiency),
                '{:.3f}'.format(cpu_efficiency), ', '.join(reason))

    table.p()


def records(options):
    db = uge.connect_database(options.database)
    with open(os.path.join(os.environ['SGE_ROOT'], os.environ['SGE_CELL'],
                           'common/accounting'),
              errors='ignore') as f:
        uge.load_data(db, f)
    data = uge.get_recent_data(db,
                               owner=options.user,
                               days=options.days,
                               hours=options.hours,
                               succeeded_only=options.succeeded_only,
                               failed_only=options.failed_only)

    if options.tab_table:
        table = printtable.TabTable()
        table.add_row('owner', 'hostname', 'job number', 'job name', 'slots',
                      'wallclock', 'user cpu', 'system cpu', 'submission',
                      'start', 'finished', 'mem req', 's_vmem', 'maxvmem',
                      'mem use%', 'cpu use%', 'exit_status', 'failed')
    else:
        table = printtable.PrettyTable()
        table.add_row('owner', 'hostname', 'job number', 'job name', 'slots',
                      'wallclock', 'user cpu', 'system cpu', 'submission',
                      'start', 'finished', 'mem req', 's_vmem', 'maxvmem',
                      'mem use%', 'cpu use%', 'exit_status', 'failed')

    for one in data:
        one = uge.add_info_to_record(dict(one))

        table.add_row(
            one['owner'], one['hostname'], one['job_id'],
            one['job_name'], one['slots'],
            duration(datetime.timedelta(seconds=one['wallclock'])),
            duration(datetime.timedelta(seconds=one['ru_utime'])),
            duration(datetime.timedelta(seconds=one['ru_stime'])),
            datetime.datetime.fromtimestamp(
                one['submission_time'] / 1000).strftime('%Y/%m/%d %H:%M:%S'),
            datetime.datetime.fromtimestamp(
                one['start_time'] / 1000).strftime('%Y/%m/%d %H:%M:%S'),
            datetime.datetime.fromtimestamp(
                one['end_time'] / 1000).strftime('%Y/%m/%d %H:%M:%S'),
            uge.human_memory_display(one['total_mem_req']),
            uge.human_memory_display(one['total_s_vmem']),
            uge.human_memory_display(int(one['maxvmem'])),
            '{:.1f}%'.format(one['memory_use%']),
            '{:.1f}%'.format(one['cpu_use%']), one['exit_status'],
            one['failed'])

    table.p()


def tablist(options):
    jobs = uge.qstat()

    now = datetime.datetime.now()
    table = printtable.TabTable()
    for one in jobs:
        if (one['owner'] == options.user
                or options.user == '*') and (one['state'] == options.state
                                             or options.state == '*'):
            if 'start_time' in one:
                time_display = duration(now - one['start_time'])
            else:
                time_display = duration(now - one['submission_time'])
            table.add_row(one['owner'], one['state'], one['priority'],
                          one.get('queue_name', ''),
                          one['job_id'], one['name'], one['slots'],
                          one.get('tasks', ''), time_display)
    table.p()


def stat(options):
    jobs = uge.qstat()
    running = collections.defaultdict(int)
    queued = collections.defaultdict(int)
    hold_queued = collections.defaultdict(int)
    running_slots = collections.defaultdict(int)
    queued_slots = collections.defaultdict(int)
    hold_queued_slots = collections.defaultdict(int)

    now = datetime.datetime.now()
    running_jobs = printtable.PrettyTable()
    running_jobs.add_row('Owner', 'Queue', 'JobID', 'Name', 'Slots',
                         'Running Time')
    for one in jobs:
        if (one['owner'] == options.user
                or options.user == '*') and (one['state'] == 'r'
                                             or one['state'] == 'Rr'):
            running_jobs.add_row(one['owner'], one['queue_name'],
                                 one['job_id'], one['name'], one['slots'],
                                 duration(now - one['start_time']))
    if len(running_jobs.rows) > 1:
        print('-- Running jobs ---------------------------')
        running_jobs.p()

    queued_jobs = printtable.PrettyTable()
    queued_jobs.add_row('Owner', 'JobID', 'Name', 'Slots', 'Tasks',
                        'Waiting time')
    for one in jobs:
        if (one['owner'] == options.user
                or options.user == '*') and one['state'] == 'qw':
            queued_jobs.add_row(one['owner'], one['job_id'], one['name'],
                                one['slots'], one.get('tasks', ''),
                                duration(now - one['submission_time']))
    if len(queued_jobs.rows) > 1:
        print('-- Queued jobs ---------------------------')
        queued_jobs.p()

    hold_queued_jobs = printtable.PrettyTable()
    hold_queued_jobs.add_row('Owner', 'JobID', 'Name', 'Slots', 'Tasks',
                             'Waiting time')
    for one in jobs:
        if (one['owner'] == options.user
                or options.user == '*') and one['state'] == 'hqw':
            hold_queued_jobs.add_row(one['owner'], one['job_id'], one['name'],
                                     one['slots'], one.get('tasks', ''),
                                     duration(now - one['submission_time']))
    if len(hold_queued_jobs.rows) > 1:
        print('-- Hold Queued jobs ---------------------------')
        hold_queued_jobs.p()

    for one in jobs:
        if one['state'] == 'r' or one['state'] == 'Rr':
            running[one['owner']] += 1
            running_slots[one['owner']] += int(one['slots'])
        elif one['state'] == 'qw':
            queued[one['owner']] += 1
            queued_slots[one['owner']] += int(one['slots'])
        elif one['state'] == 'hqw':
            hold_queued[one['owner']] += 1
            hold_queued_slots[one['owner']] += int(one['slots'])

    users = list(
        set(running.keys()) | set(queued.keys()) | set(hold_queued.keys()))
    users.sort(key=lambda x:
               (running_slots[x], queued_slots[x], hold_queued_slots[x]),
               reverse=True)

    print(' ====== Summary =======')
    summary = printtable.PrettyTable()
    summary.add_row('User', 'Running slots', 'Running jobs', 'Queued slots',
                    'Queued jobs', 'Hold slots', 'Hold jobs')
    for one in users:
        summary.add_row(one, running_slots[one], running[one],
                        queued_slots[one], queued[one], hold_queued_slots[one],
                        hold_queued[one])
    summary.p()


if __name__ == '__main__':
    _main()
