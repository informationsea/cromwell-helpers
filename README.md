# Cromwell Helper

Utilities for
[Cromwell workflow engine](https://github.com/broadinstitute/cromwell)

## cromwell-cli

Command line client for Cromwell REST API

### Commands

- backends: Show supported backends
- submit: Submit workflow
- describe: Describe workflow
- query: Query workflow status
- output: Show workflow output paths
- abort: Abort workflow
- release-hold: Release hold workflow
- metadata: Show metadata of workflow
- export: Export output data into a directory

### Configuration

1. Create `~/.cromwell/cli-config.json`
2. Write as below.

```
{
    "host": "CROMWELL HOSTNAME",
    "password": "BASIC AUTH PASSWORD IF NEEDED"
}
```

### Basic usage

1. Start cromwell server
2. Submit workflow with `cromwell-cli.py submit`
3. Check status with `cromwell-cli.py query`
4. Check detail with `cromwell-cli.py metadata`
5. Show failed task in workflow with `cromwell-cli.py meatadata -f ID`

## fakedocker

Bridge between singularity and cromwell

### Commands

- pull: pull image from docker hub and store to home directory
- images: list up downloaded images
- run-with-cromwell: run singularity in cromwell
- find: print a singularity image path for the name
- import-singularity: import singularity image to home directory

### Basic usage

1. Pull images with `pull` command
2. Make a symbolic link `docker` to `fakedocker`.
3. Add `docker` located directory to `$PATH`
4. Run cromwell server
