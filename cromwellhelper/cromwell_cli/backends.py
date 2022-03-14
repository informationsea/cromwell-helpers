import requests


def set_argument_parser(subparsers) -> None:
    backend_parser = subparsers.add_parser('backends',
                                           help='Supported backends')
    backend_parser.set_defaults(func=backends)


def backends(options):
    result = requests.get(options.host + '/api/workflows/v1/backends',
                          auth=('cromwell', options.password)).json()
    print('   Default backend: ', result['defaultBackend'])
    print('Supported backends: ', ', '.join(result['supportedBackends']))
