import requests


def set_argument_parser(subparsers) -> None:
    abort_parser = subparsers.add_parser('abort', help='Abort workflow')
    abort_parser.set_defaults(func=abort)
    abort_parser.add_argument('id', help='Execution ID')


def abort(options):
    result = requests.post(options.host +
                           '/api/workflows/v1/{}/abort'.format(options.id),
                           auth=('cromwell', options.password))
    print(result)
    print(result.json())
