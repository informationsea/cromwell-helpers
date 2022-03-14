import os
import sys
import shutil
import requests
import cromwellhelper.fileutils as fileutils


def set_argument_parser(subparsers) -> None:
    export_parser = subparsers.add_parser(
        'export', help='Export output data into a directory')
    export_parser.set_defaults(func=export)
    export_parser.add_argument('id', help='Execution ID')
    export_parser.add_argument('--output',
                               '-o',
                               help='Output directory',
                               required=True)


def export(options):
    result = requests.get(options.host +
                          '/api/workflows/v1/{}/metadata'.format(options.id),
                          auth=('cromwell', options.password))
    json_result = result.json()
    output_candidates = {}
    for call_key, call_value in json_result['calls'].items():
        for one_value in call_value:
            for one_output in collect_files(one_value['outputs']):
                if not isinstance(one_output,
                                  str) or not one_output.startswith('/'):
                    continue

                if 'callRoot' in one_value:
                    output_root = os.path.join(one_value['callRoot'],
                                               'execution')
                else:
                    output_root = search_call_root(os.path.dirname(one_output))

                output_candidates[one_output] = os.path.relpath(
                    one_output, output_root)

    if not os.path.exists(options.output):
        os.makedirs(options.output)

    for one_output in collect_files(json_result['outputs']):
        if one_output not in output_candidates:
            print('Not found: ', one_output)
        output_path = os.path.join(options.output,
                                   output_candidates[one_output])
        dirname = os.path.dirname(output_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if os.path.exists(output_path):
            print(output_path + " is already exists", file=sys.stderr)
            exit(1)

        try:
            os.link(fileutils.realpath(one_output), output_path)
        except Exception:
            shutil.copyfile(fileutils.realpath(one_output), output_path)


def search_call_root(filepath: str) -> str:
    while True:
        if filepath == '/':
            return filepath
        if os.path.basename(filepath) == 'execution':
            return filepath
        filepath = os.path.dirname(filepath)


def collect_files(output_obj):
    result = []
    if isinstance(output_obj, dict):
        for one in output_obj.values():
            result += collect_files(one)
    if isinstance(output_obj, list):
        for one in output_obj:
            result += collect_files(one)
    if isinstance(output_obj, set):
        for one in output_obj:
            result += collect_files(one)
    if isinstance(output_obj, str):
        if output_obj.startswith('/'):
            result.append(output_obj)
    return result
