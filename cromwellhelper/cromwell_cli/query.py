import requests
import json
from cromwellhelper.cromwell_cli.utils import print2, convert_localtime


def set_argument_parser(subparsers) -> None:
    query_parser = subparsers.add_parser('query', help='Query workflow status')

    query_parser.set_defaults(func=query)
    query_parser.add_argument('--name', '-n', help='Workflow name')
    query_parser.add_argument('--id', '-i', help='Execution ID')
    query_parser.add_argument('--status',
                              '-s',
                              help='Status',
                              choices=('Failed', 'Aborted', 'Succeeded',
                                       'Running', 'Submitted', 'On Hold',
                                       'Aborting'))
    query_parser.add_argument('--exclude-subworkflows',
                              '-e',
                              help='Exclude subworkflows',
                              action='store_true')
    query_parser.add_argument('--json',
                                 '-j',
                                 help='Show JSON response',
                                 action='store_true')
    query_parser.add_argument(
        '--limit',
        default=200,
        help='Number of items to show (default: %(default)s)',
        type=int)
    query_parser.add_argument('--label',
                              '-l',
                              nargs='*',
                              help='labels to require (label-key:label-value)')
    query_parser.add_argument('--exclude-label',
                              '-x',
                              nargs='*',
                              help='labels to exclude (label-key:label-value)')
    query_parser.add_argument('--submission',
                              '-m',
                              help='Oldest submission date time to query')
    query_parser.add_argument('--start',
                              '-t',
                              help='Oldest start date time to query')
    query_parser.add_argument('--end',
                              '-d',
                              help='Oldest end date time to query')
    query_parser.add_argument('--tab',
                              help='tab-delimited table',
                              action='store_true')


def query(options):
    payload = {}
    if options.name:
        payload['name'] = options.name
    if options.id:
        payload['id'] = options.id
    if options.status:
        payload['status'] = options.status
    if options.exclude_subworkflows:
        payload['includeSubworkflows'] = 'false'
    if options.submission:
        payload['submission'] = options.submission
    if options.start:
        payload['start'] = options.start
    if options.end:
        payload['end'] = options.end
    if options.label:
        payload['label'] = options.label
    if options.exclude_label:
        payload['excludeLabelOr'] = options.exclude_label

    payload['additionalQueryResultFields'] = ['labels', 'parentWorkflowId']

    response = requests.get(options.host + '/api/workflows/v1/query',
                            auth=('cromwell', options.password),
                            params=payload)
    response.raise_for_status()
    result = response.json()

    if options.json:
        print(json.dumps(result, indent='    '))
        return

    for i, one_result in enumerate(result['results']):
        if i >= options.limit:
            break

        if options.tab:
            print('\t'.join([
                one_result.get('id'),
                one_result.get('name', ''),
                one_result.get('status', ''),
                one_result.get('submission', ''),
                one_result.get('start', ''),
                one_result.get('end', ''),
                one_result.get('parentWorkflowId', '')
            ]))
        else:
            print2('        ID: {value}', one_result, 'id')
            print2('      Name: {value}', one_result, 'name')
            print2('    Status: {value}', one_result, 'status')
            print2('Submission: {value}',
                   one_result,
                   'submission',
                   value_map=convert_localtime)
            print2('     Start: {value}',
                   one_result,
                   'start',
                   value_map=convert_localtime)
            print2('       End: {value}',
                   one_result,
                   'end',
                   value_map=convert_localtime)
            print2(' Parent ID: {value}', one_result, 'parentWorkflowId')
            print2('   Root ID: {value}', one_result, 'rootWorkflowId')
            if 'labels' in one_result:
                for k, v in one_result['labels'].items():
                    if k == 'cromwell-workflow-id':
                        continue
                    print('{:>10}: {}'.format(k, v))
            print('   --------------------   ')

    print('Total:', result['totalResultsCount'])
