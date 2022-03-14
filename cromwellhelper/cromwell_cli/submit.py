import argparse
import requests
import os
import json
import sys
import zipfile
import re
import io


def set_argument_parser(subparsers) -> None:
    submit_parser = subparsers.add_parser('submit', help='Submit workflow')

    submit_parser.set_defaults(func=submit)
    submit_parser.add_argument('--input',
                               '-i',
                               type=argparse.FileType('r'),
                               help='Input JSON file',
                               nargs='*')
    submit_parser.add_argument('--labels',
                               '-l',
                               help='Labels (label-key:label-value)',
                               nargs='*')
    submit_parser.add_argument('--disable-automatic-label',
                               help='Disable automatic labels',
                               action='store_true')
    submit_parser.add_argument('--workflow',
                               '-w',
                               type=argparse.FileType('r'),
                               help='Workflow file',
                               required=True)
    submit_parser.add_argument('--workflow-type',
                               '-t',
                               choices=('auto', 'WDL', 'CWL'),
                               default='auto',
                               help='Workflow type (default:%(default)s)')
    submit_parser.add_argument('--workflow-version',
                               '-v',
                               choices=('auto', 'draft-2', 'v1.0', '1.0'),
                               default='auto',
                               help='workflow version (default:%(default)s)')
    submit_parser.add_argument('--options',
                               '-o',
                               type=argparse.FileType('r'),
                               help='Option file')
    submit_parser.add_argument('--max-retry',
                               '-m',
                               type=int,
                               help='maximum retry count')
    submit_parser.add_argument('--output', type=str, help='output directory')
    submit_parser.add_argument('--continue-while-possible',
                               action='store_true',
                               help='Continue while possible')
    submit_parser.add_argument(
        '--dependencies',
        '-d',
        type=argparse.FileType('rb'),
        help='ZIP file. Dependent workflows should be included')
    submit_parser.add_argument(
        '--auto-dependencies',
        '-a',
        action='store_true',
        help='Create dependencies zip file automatically')
    submit_parser.add_argument('--hold',
                               action='store_true',
                               help='hold',
                               default=False)


def submit(options):
    # check workflow
    workflow_data = options.workflow.read()

    workflow_version = 'draft-2'
    workflow_type = 'WDL'

    if options.workflow.name.endswith('.cwl'):
        workflow_version = 'v1.0'
        workflow_type = 'CWL'
    if workflow_data.startswith('version 1.0\n'):
        workflow_version = '1.0'

    print('Detected: {} {}'.format(workflow_type, workflow_version))

    if options.workflow_type != 'auto':
        workflow_type = options.workflow_type
    if options.workflow_version != 'auto':
        workflow_version = options.workflow_version

    file_payload = {
        'workflowSource':
        (os.path.basename(options.workflow.name), workflow_data)
    }
    # check input
    for i, one_input in enumerate(options.input):
        try:
            input_data_parsed = json.load(one_input)
        except json.decoder.JSONDecodeError as e:
            print("failed to parse JSON", one_input.name, e, file=sys.stderr)
            exit(1)

        # remove comment lines
        for delete_key in [
                x for x in input_data_parsed.keys() if x.startswith('#')
        ]:
            del input_data_parsed[delete_key]
        file_payload['workflowInputs' +
                     ('' if i == 0 else '_' + str(i + 1))] = (os.path.basename(
                         one_input.name), json.dumps(input_data_parsed))

    if options.options:
        # check json format
        try:
            options_data = json.load(options.options)
        except json.decoder.JSONDecodeError as e:
            print("failed to parse JSON",
                  options.options.name,
                  e,
                  file=sys.stderr)
            exit(1)
    else:
        options_data = {}

    if options.output:
        options_data['use_relative_output_paths'] = True
        options_data['final_workflow_outputs_dir'] = os.path.abspath(
            options.output)
    if options.max_retry:
        if 'default_runtime_attributes' not in options_data:
            options_data['default_runtime_attributes'] = {}
        options_data['default_runtime_attributes'][
            'maxRetries'] = options.max_retry
    if options.continue_while_possible:
        options_data['workflow_failure_mode'] = 'ContinueWhilePossible'

    file_payload['workflowOptions'] = ('options.json',
                                       json.dumps(options_data))

    # add label
    label_data = dict()

    if options.labels:
        for one_label in options.labels:
            elements = one_label.split(':')
            if len(elements) != 2:
                print('Invalid label format:', one_label, file=sys.stderr)
                print('Label format should be: label-key:label-value',
                      file=sys.stderr)
                exit(1)
            label_data[elements[0]] = elements[1]

    if not options.disable_automatic_label:
        label_data['workflow_path'] = os.path.abspath(options.workflow.name)
        for i, one_input in enumerate(options.input):
            label_data['input_' + str(i + 1)] = os.path.abspath(one_input.name)
        file_payload['labels'] = ('labels.json', json.dumps(label_data))

    if options.dependencies:
        file_payload['workflowDependencies'] = (os.path.basename(
            options.dependencies.name), options.dependencies)

    if options.auto_dependencies:
        dependent_files = parse_workflow(
            os.path.dirname(options.workflow.name), options.workflow.name,
            workflow_data)
        zipdata = io.BytesIO()
        with zipfile.ZipFile(
                zipdata, 'w',
                compression=zipfile.ZIP_DEFLATED) as zipfile_handle:
            for name, data in dependent_files:
                zipfile_handle.writestr(name, data)
        # with open('dependency.zip', 'wb') as f:
        #     f.write(zipdata.getvalue())
        file_payload['workflowDependencies'] = ('dependency.zip',
                                                zipdata.getvalue())

    payload = {
        'workflowType': workflow_type,
        'workflowTypeVersion': workflow_version
    }
    if options.hold:
        payload['workflowOnHold'] = True

    result = requests.post(options.host + '/api/workflows/v1',
                           files=file_payload,
                           data=payload,
                           auth=('cromwell', options.password)).json()

    # print('Submit', result)
    print('Status:', result['status'])
    if 'message' in result:
        print('Message:', result['message'])
    if 'id' in result:
        print('ID:', result['id'])


IMPORT_RE = re.compile(r'import "([^"]+)"')


def parse_workflow(basedir, workflow_path, workflow_data):
    print('parsing', workflow_path)
    result = set()
    dirname = os.path.dirname(workflow_path)
    for one in IMPORT_RE.findall(workflow_data):
        new_path = os.path.join(dirname, one)
        with open(new_path, 'r') as f:
            new_data = f.read()
        result.add((os.path.relpath(new_path, basedir), new_data))
        result |= parse_workflow(basedir, new_path, new_data)
    return result
