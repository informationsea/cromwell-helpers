import requests


def set_argument_parser(subparsers) -> None:
    status_parser = subparsers.add_parser('status', help='Show status')
    status_parser.set_defaults(func=status)


def status(options):
    response = requests.get(options.host + '/engine/v1/status',
                            auth=('cromwell', options.password))
    if response.status_code == 200:
        print('OK')
    elif response.status_code == 500:
        print('NG')
    else:
        print('Unexpected status:', response.status_code)
