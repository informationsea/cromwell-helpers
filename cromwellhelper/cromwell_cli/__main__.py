#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import os.path
import json
import os
import cromwellhelper.pager as pager
import cromwellhelper.cromwell_cli.submit
import cromwellhelper.cromwell_cli.query
import cromwellhelper.cromwell_cli.metadata
import cromwellhelper.cromwell_cli.export
import cromwellhelper.cromwell_cli.describe
import cromwellhelper.cromwell_cli.release
import cromwellhelper.cromwell_cli.backends
import cromwellhelper.cromwell_cli.output
import cromwellhelper.cromwell_cli.abort
import cromwellhelper.cromwell_cli.version
import cromwellhelper.cromwell_cli.status
import cromwellhelper.cromwell_cli.list_docker
import cromwellhelper.cromwell_cli.remove_cache


CONFIG_PATH = os.path.expanduser('~/.cromwell/cli-config.json')
DEFAULT_HOST = ''
DEFAULT_PASSWORD = ''
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH) as f:
        conf = json.load(f)
        if 'host' in conf:
            DEFAULT_HOST = conf['host']
        if 'password' in conf:
            DEFAULT_PASSWORD = conf['password']


def _main():
    try:
        __main()
    except BrokenPipeError:
        # ignore broken pipe
        pass


def __main():
    parser = argparse.ArgumentParser(description="Cromwell helper")
    parser.add_argument('--host',
                        help='Cromwell server host (default: %(default)s)',
                        default=DEFAULT_HOST)
    parser.add_argument('--password', '-p', default=DEFAULT_PASSWORD)
    parser.add_argument('--no-pager',
                        help='Do not use pager',
                        action='store_true')
    subparsers = parser.add_subparsers(required=True)

    cromwellhelper.cromwell_cli.submit.set_argument_parser(subparsers)
    cromwellhelper.cromwell_cli.describe.set_argument_parser(subparsers)
    cromwellhelper.cromwell_cli.query.set_argument_parser(subparsers)
    cromwellhelper.cromwell_cli.output.set_argument_parser(subparsers)
    cromwellhelper.cromwell_cli.abort.set_argument_parser(subparsers)
    cromwellhelper.cromwell_cli.backends.set_argument_parser(subparsers)
    cromwellhelper.cromwell_cli.release.set_argument_parser(subparsers)
    cromwellhelper.cromwell_cli.metadata.set_argument_parser(subparsers)
    cromwellhelper.cromwell_cli.export.set_argument_parser(subparsers)
    cromwellhelper.cromwell_cli.version.set_argument_parser(subparsers)
    cromwellhelper.cromwell_cli.status.set_argument_parser(subparsers)
    cromwellhelper.cromwell_cli.list_docker.set_argument_parser(subparsers)
    cromwellhelper.cromwell_cli.remove_cache.set_argument_parser(subparsers)

    if len(sys.argv) == 1:
        print("subcommand is required", file=sys.stderr)
        parser.print_help()
        return

    options = parser.parse_args()
    if not options.host:
        print('Hostname is required')
        return

    pager.AutoPager(options.no_pager)
    options.func(options)


if __name__ == '__main__':
    _main()
