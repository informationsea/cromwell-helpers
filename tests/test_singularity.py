from cromwellhelper.singularity import *
from cromwellhelper.docker import *
import pytest


def test_image_path():
    assert image_path('STORE', parse_image_name('ubuntu:18.04')) == \
        'STORE/tag/ubuntu:18.04.sif'

    assert image_path('STORE', parse_image_name('library/ubuntu:18.04')) == \
        'STORE/tag/ubuntu:18.04.sif'

    assert image_path('STORE', parse_image_name('library/ubuntu@sha256:edf05697d8ea17028a69726b4b450ad48da8b29884cd640fec950c904bfb50ce')) == \
        'STORE/sha256/ubuntu@sha256:edf05697d8ea17028a69726b4b450ad48da8b29884cd640fec950c904bfb50ce.sif'

    assert image_path('STORE', parse_image_name('registry.access.redhat.com/ubi8/ubi')) == \
        'STORE/tag/registry.access.redhat.com/ubi8/ubi:latest.sif'


# def test_pull(tmpdir):
#     image_name = parse_image_name('alpine:3.10')
#     pull_image('singularity', tmpdir, image_name)
#     path = image_path(tmpdir, image_name)
#     result = subprocess.run(['singularity', 'exec', path, '/bin/cat', '/etc/alpine-release'], capture_output=True)
#     assert result.stdout.decode('utf-8').startswith('3.10')
#     
#     #pull_image('singularity', tmpdir, parse_image_name('alpine:3.11'))


def test_update_tag_link(tmpdir):
    update_tag_link(
        tmpdir, parse_image_name('alpine:3.11'),
        parse_image_name(
            'alpine@sha256:ab00606a42621fb68f2ed6ad3c88be54397f981a7b70a79db3d1172b11c4367d'
        ))
    assert '../sha256/alpine@sha256:ab00606a42621fb68f2ed6ad3c88be54397f981a7b70a79db3d1172b11c4367d.sif' == os.readlink(
        os.path.join(tmpdir, 'tag', 'alpine:3.11.sif'))

    update_tag_link(
        tmpdir, parse_image_name('alpine:3.11'),
        parse_image_name(
            'alpine@sha256:ab00606a42621fb68f2ed6ad3c88be54397f981a7b70a79db3d1172b11c43670'
        ))
    assert '../sha256/alpine@sha256:ab00606a42621fb68f2ed6ad3c88be54397f981a7b70a79db3d1172b11c43670.sif' == os.readlink(
        os.path.join(tmpdir, 'tag', 'alpine:3.11.sif'))

    with open(os.path.join(tmpdir, 'tag', 'alpine:3.10.sif'), 'w') as f:
        f.write('dummy')

    with pytest.raises(FileExistsError):
        update_tag_link(
            tmpdir, parse_image_name('alpine:3.10'),
            parse_image_name(
                'alpine@sha256:7c3773f7bcc969f03f8f653910001d99a9d324b4b9caa008846ad2c3089f5a5f'
            ))


def test_list_images():
    testfiles_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 "testfiles", "singularity")
    images = list_images(testfiles_dir)

    assert images == {
        parse_image_name('alpine@sha256:ddba4d27a7ffc3f86dd6c2f92041af252a1f23a8e742c90e6e1297bfa1bc0c45'):
        {parse_image_name('alpine:3.11')},
        parse_image_name('alpine@sha256:de78803598bc4c940fc4591d412bffe488205d5d953f94751c6308deeaaa7eb8'):
        {parse_image_name('alpine:3.10')},
        parse_image_name('busybox@sha256:edafc0a0fb057813850d1ba44014914ca02d671ae247107ca70c94db686e7de6'):
        {
            parse_image_name('busybox:1.31'),
            parse_image_name('busybox:1'),
            parse_image_name('busybox:latest')
        },
        parse_image_name('informationsea/csv2xlsx@sha256:c4a22a2b3ad2bca31689f7dc6f77312b3136e84e1802097cec786098ab132b45'):
        {parse_image_name('informationsea/csv2xlsx:0.2.2')},
        parse_image_name('informationsea/vcfanno@sha256:276e99d3faf097b2efc2b192fe1a4d56acd0a550f6170c88440eb71b1e26db74'):
        {
            parse_image_name(
                'informationsea/vcfanno:v0.3.2-with-python-bcftools')
        }
    }
