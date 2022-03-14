import os
import os.path
import subprocess
import sys
import typing

import cromwellhelper.docker as docker
import cromwellhelper.fileutils as fileutils


def image_path(store_path: str, image_name: docker.ImageName) -> str:
    if image_name.is_tag:
        return os.path.join(
            store_path, 'tag',
            image_name.display_name + ":" + image_name.reference + ".sif")
    return os.path.join(
        store_path, 'sha256',
        image_name.display_name + "@" + image_name.reference + ".sif")


def pull_image(singularity_executable: str, store_path: str,
               image_name: docker.ImageName) -> None:
    if image_name.is_tag:
        manifest = docker.get_manifest(image_name)
        hash_name = docker.ImageName(image_name.registry, image_name.name,
                                     manifest.sha256hash, False,
                                     image_name.display_name)
    else:
        hash_name = image_name

    hash_path = os.path.abspath(image_path(store_path, hash_name))
    print(hash_path)
    if os.path.exists(hash_path):
        if image_name.is_tag:
            update_tag_link(store_path, image_name, hash_name)
        print('Image is up to date', file=sys.stderr)
        return

    os.makedirs(os.path.dirname(hash_path), exist_ok=True)
    subprocess.call([
        singularity_executable, 'build', hash_path, 'docker://' +
        hash_name.registry + '/' + hash_name.name + "@" + hash_name.reference
    ])
    if image_name.is_tag:
        update_tag_link(store_path, image_name, hash_name)


def update_tag_link(store_path: str, tag_name: docker.ImageName,
                    hash_name: docker.ImageName) -> None:
    assert tag_name.is_tag
    assert not hash_name.is_tag

    tag_path = os.path.abspath(image_path(store_path, tag_name))
    hash_path = os.path.abspath(image_path(store_path, hash_name))

    if os.path.islink(tag_path):
        if os.path.abspath(fileutils.readlink_abs(tag_path)) == hash_path:
            # update path is not required
            return
        os.remove(tag_path)

    os.makedirs(os.path.dirname(tag_path), exist_ok=True)
    fileutils.create_relative_symlink(hash_path, tag_path)
    print("link {} => {}".format(tag_path, hash_path))


def list_images(
        store_path: str
) -> typing.Dict[docker.ImageName, typing.Set[docker.ImageName]]:
    store_path = os.path.realpath(store_path)
    tag_base = os.path.join(store_path, 'tag')
    hash_base = os.path.join(store_path, 'sha256')

    hash_to_tag: typing.Dict[docker.ImageName, typing.Set[docker.
                                                          ImageName]] = dict()

    for root, dirs, files in os.walk(hash_base):
        for one_file in files:
            one_path = os.path.join(root, one_file)
            if not one_file.endswith('.sif'):
                continue
            hash_name = docker.parse_image_name(
                os.path.relpath(one_path, hash_base)[:-len('.sif')])
            hash_to_tag[hash_name] = set()

    for root, dirs, files in os.walk(tag_base):
        for one_file in files:
            one_path = os.path.join(root, one_file)
            if not one_file.endswith('.sif') or not os.path.islink(one_path):
                continue
            hash_path = fileutils.readlink_abs(one_path)
            if not hash_path.endswith('.sif'):
                continue
            if not os.path.exists(hash_path):
                print('broken link: {} -> {}'.format(one_path, hash_path),
                      file=sys.stderr)
                continue

            tag_name = docker.parse_image_name(
                os.path.relpath(one_path, tag_base)[:-len('.sif')])
            hash_name = docker.parse_image_name(
                os.path.relpath(fileutils.realpath(one_path),
                                hash_base)[:-len('.sif')])
            hash_to_tag[hash_name].add(tag_name)

    return hash_to_tag
