import requests


def set_argument_parser(subparsers) -> None:
    version_parser = subparsers.add_parser('version', help='Show version')
    version_parser.set_defaults(func=version)


def version(options):
    response = requests.get(options.host + '/engine/v1/version',
                            auth=('cromwell', options.password))
    response.raise_for_status()
    print(response.json()['cromwell'])
