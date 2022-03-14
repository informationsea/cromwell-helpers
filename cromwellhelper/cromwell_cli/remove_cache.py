import requests
import json
import os
import os.path
import typing

def set_argument_parser(subparsers) -> None:
    remove_cache_parser = subparsers.add_parser('remove-cache', help='Remove cache directory')
    remove_cache_parser.set_defaults(func=remove_cache)
    remove_cache_parser.add_argument('cromwell_executions')

def remove_cache(options):

    #print(result)
    if len(result['results']) != result['totalResultsCount']:
        print('Too many running jobs', result['totalResultsCount'])
        exit(1)

#    if os.path.basename(options.cromwell_executions) != 'cromwell-executions':
#        print('Invalid cromwell executions directory:', options.cromwell_executions)
#        exit(1)

    cromwell_root_dir = os.path.abspath(options.cromwell_executions)
    print(cromwell_root_dir)

    for root, dirs, files in os.walk(cromwell_root_dir):
        print(root)
        if root == cromwell_root_dir:
            continue
        if os.path.dirname(root) != cromwell_root_dir:
            del dirs[:]
            continue
        print(root, dirs)
        del dirs[:]
            
    print('end')
        

def query_for_status(options: typing.Any, status: str) -> typing.Dict[str, typing.Any]:
    payload = {
        'status': status,
        'additionalQueryResultFields': ['labels', 'parentWorkflowId'],
        'includeSubworkflows': 'false'
    }

    response = requests.get(options.host + '/api/workflows/v1/query',
                            auth=('cromwell', options.password),
                            params=payload)
    response.raise_for_status()
    result = response.json()

    if len(result['results']) != result['totalResultsCount']:
        print('Too many jobs', result['totalResultsCount'])
        raise Exception('Too many jobs for ' + status)

    return result
