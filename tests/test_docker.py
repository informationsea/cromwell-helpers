from cromwellhelper.docker import *


def test_parse_image_name():
    assert ImageName('registry-1.docker.io', 'library/ubuntu', '18.04', True, 'ubuntu') == \
        parse_image_name('ubuntu:18.04')

    assert ImageName('registry-1.docker.io', 'library/ubuntu', '18.04', True, 'ubuntu') == \
        parse_image_name('library/ubuntu:18.04')

    assert ImageName('registry-1.docker.io', 'library/ubuntu', '18.04', True, 'ubuntu') == \
        parse_image_name('registry-1.docker.io/library/ubuntu:18.04')

    assert ImageName('registry-1.docker.io', 'library/ubuntu', 'sha256:edf05697d8ea17028a69726b4b450ad48da8b29884cd640fec950c904bfb50ce', False, 'ubuntu') == \
        parse_image_name('ubuntu@sha256:edf05697d8ea17028a69726b4b450ad48da8b29884cd640fec950c904bfb50ce')

    assert ImageName('registry-1.docker.io', 'informationsea/manta', '1.6.0', True, 'informationsea/manta') == \
        parse_image_name('informationsea/manta:1.6.0')

    assert ImageName('hoge.foo', 'bar', 'latest', True, 'hoge.foo/bar') == \
        parse_image_name('hoge.foo/bar')


def test_api_call():
    result, token = docker_api_call("https://registry-1.docker.io/v2/")
    assert result.status_code == 200
    assert token != None


def test_get_manifest():
    manifest = get_manifest(
        ImageName(
            "registry-1.docker.io", "library/ubuntu",
            "sha256:edf05697d8ea17028a69726b4b450ad48da8b29884cd640fec950c904bfb50ce",
            False, 'ubuntu'))
    assert manifest.sha256hash == "sha256:edf05697d8ea17028a69726b4b450ad48da8b29884cd640fec950c904bfb50ce"
    assert hashlib.sha256(manifest.manifest_json.encode('utf-8')).hexdigest() == \
        "edf05697d8ea17028a69726b4b450ad48da8b29884cd640fec950c904bfb50ce"

    manifest = get_manifest(
        ImageName("registry-1.docker.io", "informationsea/manta", "1.6.0",
                  True, "informationsea/manta"))
    assert manifest.sha256hash == "sha256:5f8d0e0dd32872b6b730a611fda08c81fb366081ca20ed616e39135ec4e79e34"

    manifest = get_manifest(
        ImageName(
            'registry.access.redhat.com', 'ubi8/ubi',
            'sha256:a84f525457eb91230e62cdf9315dedac431c935f2d8ca115b0b84cecafe67dba',
            False, 'registry.access.redhat.com/ubi8/ubi'))
    assert manifest.sha256hash == 'sha256:a84f525457eb91230e62cdf9315dedac431c935f2d8ca115b0b84cecafe67dba'

    manifest = get_manifest(
        ImageName(
            'gcr.io', 'google-containers/cloud-controller-manager-amd64',
            'sha256:7a6fd3b689d0f98a11b44a40c6641eeb56aa370b4b54623958eddf52034c2c09',
            False, 'gcr.io/google-containers/cloud-controller-manager-amd64'))
    assert manifest.sha256hash == 'sha256:7a6fd3b689d0f98a11b44a40c6641eeb56aa370b4b54623958eddf52034c2c09'
