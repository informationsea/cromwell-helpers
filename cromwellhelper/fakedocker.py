#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import os.path
import sys
import subprocess
import datetime
import hashlib
import collections
import cromwellhelper.printtable as printtable
import cromwellhelper.humanize as humanize
import cromwellhelper.singularity as singularity
import cromwellhelper.docker as docker
import cromwellhelper.fileutils as fileutils
import shutil
import re
import tarfile


DockerImage = collections.namedtuple(
    'DockerImage', ['registry', 'name', 'reference', 'is_tag', 'fullname'])


def _main():
    try:
        __main()
    except BrokenPipeError:
        # ignore broken pipe
        pass


def __main():
    parser = argparse.ArgumentParser(
        description="Singularity based fake docker")
    parser.add_argument('--offline', action='store_true')
    parser.add_argument(
        '--image-store-path',
        default=os.path.expanduser('~/.cromwell/singularity'),
        help='Singularity image store path (default:%(default)s)')
    parser.add_argument(
        '--singularity-executable',
        default='singularity',
        help='Path to singularity executable (default: %(default)s)')
    parser.add_argument('--default-registry',
                        default='registry-1.docker.io',
                        help='Default registry (default: %(default)s)')
    parser.set_defaults(func=None)
    subparsers = parser.add_subparsers()

    pull_parser = subparsers.add_parser('pull', help='pull')
    pull_parser.set_defaults(func=pull)
    pull_parser.add_argument('image_name',
                             help='Image name (NAME[:TAG|@DIGEST])')

    images_parser = subparsers.add_parser('images', help='list docker images')
    images_parser.set_defaults(func=images)
    images_parser.add_argument('--format', help='print format')
    images_parser.add_argument('--digests', action='store_true')

    run_parser = subparsers.add_parser('run', help='run image')
    run_parser.set_defaults(func=run)
    run_parser.add_argument('--volume',
                            '-v',
                            help='bind volumes',
                            action='append')
    run_parser.add_argument('--publish',
                            '-p',
                            help='(not supported)',
                            action='append')
    run_parser.add_argument('--tty',
                            '-t',
                            help='(not supported)',
                            action='store_true')
    run_parser.add_argument('--interactive',
                            '-i',
                            help='(not supported)',
                            action='store_true')
    run_parser.add_argument('--rm',
                            help='(not supported)',
                            action='store_true')
    run_parser.add_argument('--workdir', '-w', help='working directory')
    run_parser.add_argument(
        '--singularity-options',
        nargs='+',
        help='options to pass singularity (default:%(default)s)',
        default=["--no-home", "--contain"])
    run_parser.add_argument('image', help='Image name (NAME[:TAG|@DIGEST])')
    run_parser.add_argument('options', help='arguments', nargs='*')

    cromwell_singularity_run_parser = subparsers.add_parser(
        'run-with-cromwell', help='run singularity in cromwell task')
    cromwell_singularity_run_parser.set_defaults(func=cromwell_singularity_run)
    cromwell_singularity_run_parser.add_argument('--workdir',
                                                 help='{cwd}',
                                                 required=True)
    cromwell_singularity_run_parser.add_argument('--docker-workdir',
                                                 help='{docker_cwd}',
                                                 required=True)
    cromwell_singularity_run_parser.add_argument('--jobshell',
                                                 help='{job_shell}',
                                                 required=True)
    cromwell_singularity_run_parser.add_argument('--script',
                                                 help='{script}',
                                                 required=True)
    cromwell_singularity_run_parser.add_argument('--image-name',
                                                 help='{docker}',
                                                 required=True)
    cromwell_singularity_run_parser.add_argument('--run-shell',
                                                 action='store_true')
    cromwell_singularity_run_parser.add_argument('--ref-cache',
                                                 help='htslib REF_CACHE directory (default: %(default)s)',
                                                 default="/share1/public/hts-ref")

    find_parser = subparsers.add_parser('find', help='find singularity image')
    find_parser.set_defaults(func=find)
    find_parser.add_argument('image', help='Image name (NAME[:TAG|@DIGEST])')

    import_parser = subparsers.add_parser(
        'import-singularity', help='import singularity image into image store')
    import_parser.set_defaults(func=import_singularity)
    import_parser.add_argument('name', help='Image name (NAME[:TAG|@DIGEST])')
    import_parser.add_argument('image_file', help='SIF singularity image file')

    memory_per_core_parser = subparsers.add_parser(
        'memory-per-core', help='Calculate memory size per CPU core')
    memory_per_core_parser.set_defaults(func=memory_per_core_run)
    memory_per_core_parser.add_argument('--workdir', help='working directory',
                                        required=True)
    memory_per_core_parser.add_argument('memory',
                                        help='total memory size in GB',
                                        type=float)
    memory_per_core_parser.add_argument('--memory-limit',
                                        help='maximum memory size in GB',
                                        type=int,
                                        default=500)
    memory_per_core_parser.add_argument('core', help='number of cpu cores',
                                        type=int)


    archive_image_parser = subparsers.add_parser("archive-images", help='Create tar archive for image files')
    archive_image_parser.set_defaults(func=archive_images)
    archive_image_parser.add_argument('images', nargs='+', help='image names')
    archive_image_parser.add_argument('--output', '-o', help='Output path', required=True)

    options = parser.parse_args()
    if not options.func:
        print('No command provieded.', file=sys.stderr)
        parser.print_usage()
        sys.exit(1)
        return

    os.makedirs(options.image_store_path, exist_ok=True)
    os.makedirs(os.path.join(options.image_store_path, 'tag'), exist_ok=True)
    os.makedirs(os.path.join(options.image_store_path, 'sha256'),
                exist_ok=True)

    options.func(options)


ATTEMPT_MAPTCH = re.compile(r"/attempt-(\d+)")


def memory_per_core_run(options):
    match = ATTEMPT_MAPTCH.search(options.workdir)
    if match:
        multiple = int(match.group(1))
    else:
        multiple = 1
    required_mem = multiple * options.memory
    if required_mem > options.memory_limit:
        required_mem = options.memory_limit

    print("{:.0f}".format(required_mem / options.core * 1024))


def cromwell_singularity_run(options):
    # search "cromwell-execution" directory
    workdir = fileutils.realpath(options.workdir)
    execution_dir = fileutils.realpath(os.path.abspath(options.workdir))
    while execution_dir and execution_dir != '/':
        if os.path.basename(execution_dir) == 'cromwell-executions':
            break
        execution_dir = os.path.dirname(execution_dir)
    logfile = open(os.path.join(workdir, 'fakedocker.log'), 'w')

    # create bind parameter
    BAD_CHARS = [',', ':', ' ']
    binds = {
        (options.script, options.script, options.script),
    }
    binds |= set(fileutils.search_symlinks(os.path.join(workdir, 'inputs')))

    for one_pair in binds:
        # print('PAIR: {}'.format(one_pair[0]), file=sys.stderr)
        # print('   => {}'.format(one_pair[1]), file=sys.stderr)
        # print('   => {}'.format(one_pair[2]), file=sys.stderr)
        for one_path in one_pair:
            for one_bad in BAD_CHARS:
                if one_bad in one_path:
                    print('Bad char is included in path name:',
                          one_path,
                          file=sys.stderr)
                    sys.exit(1)

    bind_arg = ','.join([x[2] + ':' + x[1] + ':ro' for x in binds])
    # print(bind_arg.replace(',', '\n'), file=sys.stderr)

    ACCEPT_BIND_LEN = 100000

    if len(bind_arg) > ACCEPT_BIND_LEN:
        bind_arg = ','.join([
            x[2] + ':' + x[1] + ':ro' for x in binds
            if not x[0].startswith(execution_dir) or not x[1].startswith(execution_dir)
        ])

        if bind_arg:
            bind_arg += ','
        bind_arg += '{}:{}:ro'.format(execution_dir, execution_dir)
        # print(bind_arg.replace(',', '\n'))
    if bind_arg:
        bind_arg += ','
    bind_arg += '{}:{}:rw,'.format(workdir, options.docker_workdir)
    bind_arg += '{0}:{0}:rw,'.format(os.path.join(workdir, 'home'))

    if os.path.exists(options.ref_cache):
        bind_arg += f'{options.ref_cache}:/hts-ref:ro'
        os.environ['REF_CACHE'] = "/hts-ref/%2s/%2s/%s"

    print('actual bind', bind_arg, file=logfile)
    logfile.flush()

    # find singularity image
    image = docker.parse_image_name(options.image_name,
                                    options.default_registry)
    image_path = singularity.image_path(options.image_store_path, image)
    if os.path.islink(image_path):
        image_path = fileutils.realpath(image_path)
    if not os.path.isfile(image_path):
        print('image file is not found', file=sys.stderr)
        sys.exit(1)

    # create directories
    os.makedirs(os.path.join(workdir, 'home'), exist_ok=True)
    os.makedirs(os.path.join(workdir, 'tmp'), exist_ok=True)

    args = [
        options.singularity_executable, 'exec', '--no-home', '--home',
        os.path.join(workdir, 'home'), '--workdir',
        os.path.join(workdir, 'tmp'), '--bind', bind_arg, image_path,
        options.jobshell, options.script
    ]
    if options.run_shell:
        args = args[:-1]

    sys.stderr.flush()
    result = subprocess.run(args, cwd=workdir)
    sys.exit(result.returncode)


def archive_images(options):
    with tarfile.TarFile(options.output, 'w') as f:
        for one in options.images:
            image = docker.parse_image_name(one, options.default_registry)
            image_path = os.path.abspath(
                singularity.image_path(options.image_store_path, image))
            store_path = singularity.image_path('.cromwell/singularity', image)
            # print(image_path, store_path)
            f.add(image_path, store_path)

            if os.path.islink(image_path):
                image_path = fileutils.realpath(image_path)
                store_path = os.path.join('.cromwell/singularity', os.path.relpath(image_path, fileutils.realpath(options.image_store_path)))
            if os.path.exists(image_path):
                f.add(image_path, store_path)
                # print(image_path, store_path)


def run(options):
    image = docker.parse_image_name(options.image, options.default_registry)
    image_path = os.path.abspath(
        singularity.image_path(options.image_store_path, image))
    if os.path.islink(image_path):
        image_path = fileutils.realpath(image_path)
    if not os.path.exists(image_path):
        print('image file is not found', file=sys.stderr)
        sys.exit(1)

    print('not implemented', file=sys.stderr)
    sys.exit(1)


def import_singularity(options):
    image_name = docker.parse_image_name(options.name,
                                         options.default_registry)

    if image_name.is_tag:
        with open(options.image_file, 'rb') as f:
            m = hashlib.sha256()
            while True:
                data = f.read(1024 * 1024)
                if not data:
                    break
                m.update(data)
            hashhex = 'sha256:' + m.hexdigest()
        hash_name = docker.ImageName(image_name.registry, image_name.name,
                                     hashhex, False, image_name.display_name)
    else:
        hash_name = image_name

    image_path = singularity.image_path(options.image_store_path, hash_name)
    if os.path.isfile(image_path):
        print('image file is already exists', file=sys.stderr)
        if image_name.is_tag:
            singularity.update_tag_link(options.image_store_path, image_name,
                                        hash_name)
        sys.exit(1)

    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    shutil.copyfile(options.image_file, image_path)
    with open(image_path + ".warn", "w") as f:
        print("NOT_DOWNLOADED_FROM_DOCKERHUB", file=f)

    if image_name.is_tag:
        singularity.update_tag_link(options.image_store_path, image_name,
                                    hash_name)


def find(options):
    image = docker.parse_image_name(options.image, options.default_registry)
    image_path = os.path.abspath(
        singularity.image_path(options.image_store_path, image))
    if os.path.islink(image_path):
        image_path = fileutils.realpath(image_path)
    if os.path.exists(image_path):
        print(image_path)
    else:
        print('image file is not found', file=sys.stderr)
        sys.exit(1)


def images(options):
    hash2tag = singularity.list_images(options.image_store_path)

    keys = list(hash2tag.keys())
    keys.sort(key=lambda x: x.display_name)

    if not options.digests and not options.format:
        p = printtable.PrettyTable('  ')
        p.add_row('REPOSITORY', 'TAG', 'DIGEST', 'CREATED', 'SIZE', 'WARN')

        for h in keys:
            tags = list(hash2tag[h])
            tags.sort(key=lambda x: x.reference)
            image_path = singularity.image_path(options.image_store_path, h)
            stat_result = os.stat(image_path)
            timediff = humanize.humanize_time_delta(
                datetime.datetime.now() -
                datetime.datetime.fromtimestamp(stat_result.st_mtime)) + ' ago'
            warn = os.path.exists(image_path + '.warn')

            for tag in tags:
                p.add_row(h.display_name, tag.reference, h.reference, timediff,
                          humanize.humanize_bytes(stat_result.st_size),
                          'YES' if warn else '')
            if not tags:
                p.add_row(h.display_name, '<none>', h.reference, timediff,
                          humanize.humanize_bytes(stat_result.st_size),
                          'YES' if warn else '')
        p.p()
    elif options.digests and options.format == \
            '{{printf "%s\\t%s\\t%s" .Repository .Tag .Digest}}':
        for h in keys:
            tags = list(hash2tag[h])
            tags.sort(key=lambda x: x.reference)
            for tag in tags:
                print('{}\t{}\t{}'.format(h.display_name, tag.reference,
                                          h.reference))
            # workaround for cromwell bug / cromwell cannot
            # handle image_name@sha256:HASH format correctly
            print('{}\t{}\t{}'.format(h.display_name, h.reference,
                                      h.reference))
    else:
        print('Unsupported option', repr(options.format), file=sys.stderr)
        sys.exit(1)


def pull(options):
    if options.offline:
        print('Cannot pull image without internet connection.',
              file=sys.stderr)
        sys.exit(1)
    singularity.pull_image(options.singularity_executable,
                           options.image_store_path,
                           docker.parse_image_name(options.image_name))


if __name__ == '__main__':
    _main()
