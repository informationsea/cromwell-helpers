import re
import hashlib
import typing
import requests

BEARER = re.compile(
    r'Bearer realm="([\w.\-_/:]+)",service="([\w.\-_]+)",scope="([\w:\-_./]+)"'
)
BEARER_NO_SCOPE = re.compile(
    r'Bearer realm="([\w.\-_/:]+)",service="([\w.\-_]+)"')
DEFAULT_REGISTRY = 'registry-1.docker.io'


class Manifest(typing.NamedTuple):
    sha256hash: str
    manifest_json: str
    manifest_data: typing.Any
    token: typing.Optional[str]


class ImageName(typing.NamedTuple):
    registry: str
    name: str
    reference: str
    is_tag: bool
    display_name: str


def parse_image_name(image_name: str,
                     default_registry: str = DEFAULT_REGISTRY) -> ImageName:
    name = image_name
    if '@' in name:
        (name, reference) = name.split("@", 1)
        tag = False
    elif ':' in name:
        (name, reference) = name.split(":", 1)
        tag = not reference.startswith('sha256:')
    else:
        reference = "latest"
        tag = True

    if '/' not in name:
        name = 'library/' + name

    components = name.split('/')
    if len(components) > 3:
        raise Exception('Invalid image name: ' + image_name)
    if len(components) == 3 or '.' in components[0]:
        registry = components[0]
        name = '/'.join(components[1:])
    else:
        registry = default_registry

    if registry == default_registry:
        if name.startswith('library/'):
            display_name = name[len('library/'):]
        else:
            display_name = name
    else:
        display_name = registry + '/' + name

    return ImageName(registry, name, reference, tag, display_name)


def get_manifest(image_name: ImageName,
                 token: typing.Optional[str] = None) -> Manifest:
    url = "https://{}/v2/{}/manifests/{}".format(image_name.registry,
                                                 image_name.name,
                                                 image_name.reference)
    manifest, token = docker_api_call(
        url,
        {'Accept': 'application/vnd.docker.distribution.manifest.v2+json'},
        token)

    if 'Docker-Content-Digest' in manifest.headers:
        sha256hash = manifest.headers['Docker-Content-Digest']
    else:
        sha256hash = 'sha256:' + hashlib.sha256(
            manifest.text.encode('utf-8')).hexdigest()

    return Manifest(
        sha256hash=sha256hash,
        manifest_json=manifest.text,
        manifest_data=manifest.json(),
        token=token,
    )


def docker_api_call(url: str,
                    additional_headers: dict = {},
                    token: typing.Optional[str] = None
                    ) -> typing.Tuple[requests.Response, typing.Optional[str]]:
    headers = {'Docker-Distribution-API-Version': 'registry/2.0'}
    headers.update(additional_headers)
    if token:
        headers['Authorization'] = 'Bearer ' + token

    first_try = requests.get(url, headers=headers)
    if first_try.status_code == requests.codes.ok:
        return (first_try, token)
    if first_try.status_code != 401:
        first_try.raise_for_status()

    auth_info_re = BEARER.match(first_try.headers['Www-Authenticate'])
    if auth_info_re:
        auth_params = {
            'scope': auth_info_re.group(3),
            'service': auth_info_re.group(2)
        }
    else:
        auth_info_re = BEARER_NO_SCOPE.match(
            first_try.headers['Www-Authenticate'])
        if auth_info_re:
            auth_params = {'service': auth_info_re.group(2)}
        else:
            raise Exception('Unexpected www-authenticate: {}'.format(
                first_try.headers['Www-Authenticate']))

    auth_data = requests.get(auth_info_re.group(1), params=auth_params)
    auth_data.raise_for_status()
    newtoken: str = auth_data.json()['token']
    headers['Authorization'] = 'Bearer ' + newtoken

    data = requests.get(url, headers=headers)
    data.raise_for_status()
    return (data, newtoken)
