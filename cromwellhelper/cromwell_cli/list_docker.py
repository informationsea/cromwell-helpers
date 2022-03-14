import requests
import sys


def set_argument_parser(subparsers) -> None:
    abort_parser = subparsers.add_parser('list-docker',
                                         help='List up used docker images')
    abort_parser.set_defaults(func=list_docker)
    abort_parser.add_argument('id', help='Execution ID')


def list_docker(options):
    to_process_workflow = {options.id}
    processed_workflow = set()
    docker_images = set()

    while to_process_workflow:
        target_id = to_process_workflow.pop()
        processed_workflow.add(target_id)
        new_images, new_workflows = check_workflow(options, target_id)
        docker_images |= new_images
        to_process_workflow |= new_workflows - processed_workflow

    for one in docker_images:
        print(one)
    

def check_workflow(options, workflow_id):
    result = requests.get(options.host +
                          '/api/workflows/v1/{}/metadata'.format(workflow_id),
                          auth=('cromwell', options.password))

    json_result = result.json()
    print('Checking {} / {}'.format(workflow_id, json_result['workflowName']), file=sys.stderr)
    
    sub_workflows = set()
    docker_images = set()

    for call_key, call_value in json_result['calls'].items():
        for one_value in call_value:
            if 'subWorkflowId' in one_value:
                sub_workflows.add(one_value['subWorkflowId'])
                #print('sub workflow', one_value['subWorkflowId'])

            if 'runtimeAttributes' in one_value:
                if 'docker' in one_value['runtimeAttributes']:
                    docker_images.add(one_value['runtimeAttributes']['docker'])
                    #print('docker', one_value['runtimeAttributes']['docker'])
    return (docker_images, sub_workflows)
