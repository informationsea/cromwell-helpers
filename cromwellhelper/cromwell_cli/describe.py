import argparse
import os.path
import requests
import json


def set_argument_parser(subparsers) -> None:
    describe_parser = subparsers.add_parser('describe',
                                            help='Describe workflow')

    describe_parser.set_defaults(func=describe)
    describe_parser.add_argument('--input',
                                 '-i',
                                 type=argparse.FileType('r'),
                                 help='Input JSON file')
    describe_parser.add_argument('--workflow',
                                 '-w',
                                 type=argparse.FileType('r'),
                                 help='Workflow file',
                                 required=True)
    describe_parser.add_argument('--workflow-type',
                                 '-t',
                                 choices=('WDL', 'CWL'),
                                 default='WDL',
                                 help='Workflow type (default:%(default)s)')
    describe_parser.add_argument('--workflow-version',
                                 '-v',
                                 choices=('draft-2', 'v1.0', '1.0'),
                                 default='draft-2',
                                 help='workflow version (default:%(default)s)')
    describe_parser.add_argument('--json',
                                 '-j',
                                 action='store_true',
                                 help='show as formatted JSON output')


def describe(options):
    file_payload = {
        'workflowSource':
        (os.path.basename(options.workflow.name), options.workflow)
    }
    if options.input:
        file_payload['workflowInput'] = (os.path.basename(options.input.name),
                                         options.input)
    payload = {
        'workflowType': options.workflow_type,
        'workflowTypeVersion': options.workflow_version
    }

    response = requests.post(options.host + '/api/womtool/v1/describe',
                             files=file_payload,
                             data=payload,
                             auth=('cromwell', options.password))
    # response.raise_for_status()
    result = response.json()

    if options.json:
        print(json.dumps(result, indent='  '))
        return
    response.raise_for_status()

    print('         Valid:', result['valid'])
    print('Valid Workflow:', result['validWorkflow'])
    print('   Is runnable:', result['isRunnableWorkflow'])
    print('          Name:', result['name'])
    print('        Errors:', '\n'.join(result['errors']))
    print('        Inputs:')
    for one_input in result['inputs']:
        print('            {}: {}'.format(one_input['name'],
                                          one_input['typeDisplayName']))
    print('       Outputs:')
    for one_output in result['outputs']:
        print('            {}: {}'.format(one_output['name'],
                                          one_output['typeDisplayName']))
