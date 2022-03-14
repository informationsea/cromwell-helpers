import collections
import requests
import json
from cromwellhelper.cromwell_cli.utils import print2, summarize_command,\
    convert_localtime


def set_argument_parser(subparsers) -> None:
    metadata_parser = subparsers.add_parser('metadata',
                                            help='Show metadata of workflow')

    metadata_parser.set_defaults(func=metadata)
    metadata_parser.add_argument('id', help='Execution ID')
    metadata_parser.add_argument('--json',
                                 '-j',
                                 help='Show JSON response',
                                 action='store_true')
    metadata_parser.add_argument('--failed-only',
                                 '-f',
                                 help='Show failed call only',
                                 action='store_true')


def metadata(options):
    result = requests.get(options.host +
                          '/api/workflows/v1/{}/metadata'.format(options.id),
                          auth=('cromwell', options.password))
    if options.json:
        print(json.dumps(result.json(), indent='  '))
        return
    json_result = result.json()

    state_count = collections.defaultdict(int)
    for call_key, call_value in json_result['calls'].items():
        for one in call_value:
            state_count[one['executionStatus']] += 1

    print2('       Workflow Name: {value}', json_result, 'workflowName')
    print2(' Workflow Submission: {value}',
           json_result,
           'submission',
           value_map=convert_localtime)
    print2('     Workflow Status: {value}', json_result, 'status')
    print2('      Workflow Start: {value}',
           json_result,
           'start',
           value_map=convert_localtime)
    print2('        Workflow End: {value}',
           json_result,
           'end',
           value_map=convert_localtime)
    for k, v in state_count.items():
        print('{:>20}: {}'.format("# of " + k + " jobs", v))
    if 'labels' in json_result:
        for k, v in json_result['labels'].items():
            print('{:>20}: {}'.format(k, v))

    print(' Calls: -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')
    for call_key, call_value in json_result['calls'].items():
        if options.failed_only and all(
                [x['executionStatus'] != 'Failed' for x in call_value]):
            continue

        print('   Call Name:', call_key)
        for i, one_value in enumerate(call_value):
            if options.failed_only and one_value['executionStatus'] != \
                   'Failed':
                continue

            print2('   [{:2}]       Status: {value}', one_value,
                   'executionStatus', i)
            print2('   [{:2}]        Start: {value}',
                   one_value,
                   'start',
                   i,
                   value_map=convert_localtime)
            print2('   [{:2}]          End: {value}',
                   one_value,
                   'end',
                   i,
                   value_map=convert_localtime)
            print2('   [{:2}]       Job ID: {value}', one_value, 'jobId', i)
            print2('   [{:2}]  Return Code: {value}', one_value, 'returnCode',
                   i)
            print2('   [{:2}] Command Line: {value}',
                   one_value,
                   'commandLine',
                   i,
                   value_map=summarize_command)
            print2('   [{:2}]       stdout: {value}', one_value, 'stdout', i)
            print2('   [{:2}]       stderr: {value}', one_value, 'stderr', i)
            print2('   [{:2}]      Attempt: {value}', one_value, 'attempt', i)
            print2('   [{:2}] Sub Workflow: {value}', one_value,
                   'subWorkflowId', i)

            if 'runtimeAttributes' in one_value:
                print2('   [{:2}]       docker: {value}',
                       one_value['runtimeAttributes'], 'docker', i)
                print2('   [{:2}]          CPU: {value}',
                       one_value['runtimeAttributes'], 'cpu', i)
                print2('   [{:2}]       Memory: {value}',
                       one_value['runtimeAttributes'], 'memory', i)

            if 'callCaching' in one_value:
                print2('   [{:2}] call caching: {value}',
                       one_value['callCaching'], 'result', i)

            if 'failures' in one_value and one_value['failures']:
                print('   [{:2}]  ----- Failure Messages  ----'.format(i))
                print_failure(one_value['failures'])
            print('   ------')

    if 'failures' in json_result and json_result['failures']:
        print('   ----- Failure Messages  ----')
        print_failure(json_result['failures'])
        print('   ------')


def print_failure(failures: list):
    for one in failures:
        print('    ', one['message'])
        if one['causedBy']:
            print_failure(one['causedBy'])
