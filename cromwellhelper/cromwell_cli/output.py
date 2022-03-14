import requests


def set_argument_parser(subparsers) -> None:
    output_parser = subparsers.add_parser('output',
                                          help='Show workflow output paths')
    output_parser.set_defaults(func=output)
    output_parser.add_argument('id', help='Execution ID')


def output(options):
    result = requests.get(options.host +
                          '/api/workflows/v1/{}/outputs'.format(options.id),
                          auth=('cromwell', options.password))
    for k, v in result.json()['outputs'].items():
        print('{:10}: {}'.format(k, v))
