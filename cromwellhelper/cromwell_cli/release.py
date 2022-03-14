import requests


def set_argument_parser(subparsers) -> None:
    release_parser = subparsers.add_parser('release-hold',
                                           help='Release hold workflow')
    release_parser.set_defaults(func=release_hold)
    release_parser.add_argument('id', help='Execution ID')


def release_hold(options):
    result = requests.post(
        options.host + '/api/workflows/v1/{}/releaseHold'.format(options.id),
        auth=('cromwell', options.password))
    result.raise_for_status()
    print(result.json())
