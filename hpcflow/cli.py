"""`hpcflow.cli.py`

Module that exposes a command line interface for `hpcflow`.

"""
import socket
import os
from pathlib import Path
from pprint import pprint
from datetime import datetime
from random import randint

import click

from hpcflow import __version__
from hpcflow import api


def get_process_stamp():
    return '{} {} {}'.format(
        datetime.now(),
        socket.gethostname(),
        os.getpid(),
    )


def validate_cloud_provider(ctx, param, value):

    good_providers = ['dropbox']
    if value not in good_providers:
        msg = ('`provider` must be one of: {}'.format(good_providers))
        raise click.BadParameter(msg)

    return value


def validate_task_ranges(ctx, param, value):
    """Validate the task range.

    Parameters
    ----------
    ctx
    param
    value : str
        Stringified comma-separated list, where each element indicates the
        tasks to submit for that channel of the Workflow. List elements can be
        one of:
            all
                submit all tasks in the given channel.
            n[-m[:s]]
                submit a range of tasks from task `n` to task `m`
                (inclusively), with an optional step size of `s`.
            <empty>
                submit no tasks from the given channel.

    Returns
    -------
    task_ranges : list of tuple
        (start, stop, step)

    """

    if value is None:
        return

    if ',' in value:
        value = value.split(',')
    else:
        value = [value]

    task_ranges = []
    for i in value:

        if i.strip() == 'all':
            task_ranges.append([1, -1, 1])
            continue

        elif i.strip() == '':
            task_ranges.append([])
            continue

        task_step = 1

        msg = ('Could not understand task range. It should be specified in '
               'the format: `n[-m[:s]]` where `n` is the starting task ID, `m` is '
               ' the ending task ID, and `s` is the task step size.')

        if '-' in i:
            # Task range
            task_start, task_stop = i.split('-')

            if ':' in task_stop:
                # With step size:
                task_stop, task_step = task_stop.split(':')

                try:
                    task_step = int(task_step)
                except ValueError:
                    raise click.BadParameter(msg)

            try:
                task_start = int(task_start)
                task_stop = int(task_stop)
            except ValueError:
                raise click.BadParameter(msg)

        else:
            # Single task
            try:
                task = int(i)
                task_start = task
                task_stop = task
            except ValueError:
                raise click.BadParameter(msg)

        if task_start > task_stop:
            msg = ('Task starting ID must be smaller than or equal to '
                   'task ending ID.')
            raise click.BadParameter(msg)

        task_range = [task_start, task_stop, task_step]
        task_ranges.append(task_range)

    task_ranges = task_ranges[0]  # For now - no channels.
    return task_ranges


@click.group()
@click.version_option(version=__version__)
def cli():
    pass


@cli.command()
@click.option('--yes', '-y', is_flag=True)
@click.option('--config-dir', type=click.Path(exists=True))
def clean(directory=None, yes=True, config_dir=None):
    """Clean the directory of all content generated by `hpcflow`."""
    msg = ('Do you want to remove all `hpc-flow`-generated files '
           'from {}?')
    if directory:
        msg = msg.format(directory)
    else:
        msg = msg.format('the current directory')
    if yes or click.confirm(msg):
        api.clean(dir_path=directory, config_dir=config_dir)


@cli.command()
@click.option('--directory', '-d')
@click.option('--json-file')
@click.option('--json')
@click.option('--config-dir', type=click.Path(exists=True))
@click.argument('profiles', nargs=-1, type=click.Path(exists=True))
def make(directory=None, profiles=None, json_file=None, json=None, config_dir=None):
    """Generate a new Workflow."""
    print('hpcflow.cli.make', flush=True)

    workflow_id = api.make_workflow(
        dir_path=directory,
        profile_list=profiles,
        json_file=json_file,
        json_str=json,
        config_dir=config_dir,
        clean=False,
    )
    print('Generated new Workflow with ID {}'.format(workflow_id))


@cli.command()
@click.option('--directory', '-d')
@click.option('--config-dir', type=click.Path(exists=True))
@click.argument('cmd_group_sub_id', type=click.INT)
@click.argument('task_idx', type=click.INT)
@click.argument('iter_idx', type=click.INT)
def write_runtime_files(cmd_group_sub_id, task_idx, iter_idx, directory=None,
                        config_dir=None):
    print('hpcflow.cli.write_runtime_files', flush=True)
    api.write_runtime_files(
        cmd_group_sub_id,
        task_idx,
        iter_idx,
        dir_path=directory,
        config_dir=config_dir,
    )


@cli.command()
@click.option('--directory', '-d')
@click.option('--config-dir', type=click.Path(exists=True))
@click.argument('cmd_group_sub_id', type=click.INT)
@click.argument('task_idx', type=click.INT)
@click.argument('iter_idx', type=click.INT)
def set_task_start(cmd_group_sub_id, task_idx, iter_idx, directory=None, config_dir=None):
    print('hpcflow.cli.set_task_start', flush=True)
    api.set_task_start(cmd_group_sub_id, task_idx, iter_idx, directory, config_dir)


@cli.command()
@click.option('--directory', '-d')
@click.option('--config-dir', type=click.Path(exists=True))
@click.argument('cmd_group_sub_id', type=click.INT)
@click.argument('task_idx', type=click.INT)
@click.argument('iter_idx', type=click.INT)
def set_task_end(cmd_group_sub_id, task_idx, iter_idx, directory=None, config_dir=None):
    print('hpcflow.cli.set_task_end', flush=True)
    api.set_task_end(cmd_group_sub_id, task_idx, iter_idx, directory, config_dir)


@cli.command()
@click.option('--directory', '-d')
@click.option('--config-dir', type=click.Path(exists=True))
@click.argument('cmd_group_sub_id', type=click.INT)
@click.argument('task_idx', type=click.INT)
@click.argument('iter_idx', type=click.INT)
def archive(cmd_group_sub_id, task_idx, iter_idx, directory=None, config_dir=None):
    print('hpcflow.cli.archive', flush=True)
    api.archive(
        cmd_group_sub_id,
        task_idx,
        iter_idx,
        dir_path=directory,
        config_dir=config_dir,
    )


@cli.command()
@click.option('--directory', '-d')
@click.option('--config-dir', type=click.Path(exists=True))
@click.argument('cmd_group_sub_id', type=click.INT)
@click.argument('task_idx', type=click.INT)
@click.argument('iter_idx', type=click.INT)
def get_scheduler_stats(cmd_group_sub_id, task_idx, iter_idx, directory=None,
                        config_dir=None):
    print('hpcflow.cli.get_scheduler_stats', flush=True)
    api.get_scheduler_stats(
        cmd_group_sub_id,
        task_idx,
        iter_idx,
        dir_path=directory,
        config_dir=config_dir,
    )


@cli.command()
@click.option('--directory', '-d')
@click.option('--workflow-id', '-w', type=click.INT)
@click.option('--config-dir', type=click.Path(exists=True))
def root_archive(workflow_id, directory=None, config_dir=None):
    print('hpcflow.cli.root_archive', flush=True)
    api.root_archive(
        workflow_id,
        dir_path=directory,
        config_dir=config_dir,
    )


@cli.command()
def stat():
    """Show the status of running tasks and the number completed tasks."""
    print('hpcflow.cli.stat')


@cli.command()
@click.option('--directory', '-d')
@click.option('--workflow-id', '-w', type=click.INT)
@click.option('--config-dir', type=click.Path(exists=True))
def show_stats(directory=None, workflow_id=None, config_dir=None):
    'Show task statistics, formatted as a table.'
    stats_fmt = api.get_formatted_stats(directory, workflow_id, config_dir=config_dir)
    print(stats_fmt)


@cli.command()
@click.option('--directory', '-d')
@click.option('--workflow-id', '-w', type=click.INT)
@click.option('--config-dir', type=click.Path(exists=True))
@click.argument('save_path', type=click.Path(exists=False, dir_okay=False))
def save_stats(save_path, directory=None, workflow_id=None, config_dir=None):
    'Save task statistics as a JSON file.'
    api.save_stats(save_path, directory, workflow_id, config_dir=config_dir)


@cli.command()
@click.option('--directory', '-d')
@click.option('--workflow-id', '-w', type=click.INT)
@click.option('--config-dir', type=click.Path(exists=True))
def kill(directory=None, workflow_id=None, config_dir=None):
    api.kill(directory, workflow_id, config_dir=config_dir)


@cli.command()
@click.option('--directory', '-d')
@click.option('--workflow-id', '-w', type=click.INT)
@click.option('--config-dir', type=click.Path(exists=True))
@click.option('--json-file')
@click.option('--json')
@click.option('--task-ranges', '-t',
              help=('Task ranges are specified as a comma-separated list whose'
                    ' elements are one of: "n[-m[:s]]", "all" or "" (empty)'),
              callback=validate_task_ranges)
@click.argument('profiles', nargs=-1, type=click.Path(exists=True))
def submit(directory=None, workflow_id=None, task_ranges=None, profiles=None,
           json_file=None, json=None, config_dir=None):
    """Submit(and optionally generate) a Workflow."""

    print('hpcflow.cli.submit', flush=True)

    existing_ids = api.get_workflow_ids(directory, config_dir)
    submit_args = {
        'dir_path': directory,
        'task_range': task_ranges,
        'config_dir': config_dir,
    }

    if workflow_id:
        # Submit an existing Workflow.

        if not existing_ids:
            msg = 'There are no existing Workflows in the directory {}'
            raise ValueError(msg.format(directory))

        submit_args['workflow_id'] = workflow_id

        if workflow_id not in existing_ids:
            msg = ('The Workflow ID "{}" does not match an existing Workflow '
                   'in the directory {}. Existing Workflow IDs are {}')
            raise ValueError(msg.format(workflow_id, directory, existing_ids))

        submission_id = api.submit_workflow(**submit_args)

    else:
        # First generate a Workflow, and then submit it.

        make_workflow = True
        if existing_ids:
            # Check user did not want to submit existing Workflow:
            msg = 'Previous workflows exist with IDs: {}. Add new workflow?'
            make_workflow = click.confirm(msg.format(existing_ids))

            # TODO: if `make_workflow=False`, show existing IDs and offer to
            # submit one?

        if make_workflow:
            workflow_id = api.make_workflow(
                dir_path=directory,
                profile_list=profiles,
                json_file=json_file,
                json_str=json,
                config_dir=config_dir,
            )
            print('Generated new Workflow with ID {}'.format(workflow_id))

            submit_args['workflow_id'] = workflow_id
            submission_id = api.submit_workflow(**submit_args)

        else:
            print('Exiting.')
            return

    print('Submitted Workflow (ID {}) with submission '
          'ID {}'.format(workflow_id, submission_id))


@cli.command()
@click.option('--name', '-n', required=True)
@click.option('--value', '-v', required=True)
@click.option('--config-dir', type=click.Path(exists=True))
def update_config(name, value, config_dir=None):
    api.update_config(name, value, config_dir=config_dir)


@cli.group()
def dummy():
    'Dummy commands for testing/documentation.'


@dummy.command('makeSomething')
@click.option('--name', default='infile')
@click.option('--num', type=click.INT, default=2)
@click.argument('extension', nargs=-1, default=None)
def dummy_make_something(name, num, extension):

    if not extension:
        extension = ['.txt' for i in range(num)]
    elif len(extension) != num:
        raise click.BadParameter(
            'Number of specified extensions argument must match `num` parameter.')

    for i in range(num):
        out_path = Path('{}_{}{}'.format(name, i + 1, extension[i]))
        with out_path.open('w') as handle:
            handle.write('{}\n'.format(randint(0, 1e6)))
            handle.write('{} Generated by `makeSomething --name {} --num {} {}`.'.format(
                get_process_stamp(),
                name,
                num,
                ' '.join(['"{}"'.format(j) for j in extension])
            ))


@dummy.command('doSomething')
@click.option('--infile1', '-i1', type=click.Path(exists=True), required=True)
@click.option('--infile2', '-i2', type=click.Path(exists=True), required=True)
@click.option('--value', '-v')
@click.option('--out', '-o')
def dummy_do_something(infile1, infile2, value=None, out=None):

    with Path(infile1).open('r') as handle:
        file_id_1 = int(handle.readline().strip())
    with Path(infile2).open('r') as handle:
        file_id_2 = int(handle.readline().strip())

    if out is None:
        out = 'outfile.txt'
    out_path = Path(out)
    with out_path.open('a') as handle:
        handle.write('{}\n'.format(randint(0, 1e6)))
        handle.write('{} Generated by `doSomething --infile1 {} --infile2 {}`.\n'.format(
            get_process_stamp(), infile1, infile2))
        if value:
            handle.write('{} Value: {}\n'.format(get_process_stamp(), value))
        handle.write('{} Original file ID: {}: {}\n'.format(
            get_process_stamp(), infile1, file_id_1))
        handle.write('{} Original file ID: {}: {}\n'.format(
            get_process_stamp(), infile2, file_id_2))


@dummy.command('splitSomething')
@click.argument('infile', type=click.Path(exists=True))
@click.option('--num', '-n', type=click.INT, default=2)
def dummy_split_something(infile, num):

    with Path(infile).open('r') as handle:
        file_id = int(handle.readline().strip())
    for i in range(num):
        out_path = Path('outfile_{}.txt'.format(i + 1))
        with out_path.open('w') as handle:
            handle.write('{}\n'.format(randint(0, 1e6)))
            handle.write('{} Generated by `splitSomething {}`.\n'.format(
                get_process_stamp(), infile))
            handle.write('{} Original file ID: {}: {}\n'.format(
                get_process_stamp(), infile, file_id))


@dummy.command('processSomething')
@click.argument('infile', type=click.Path(exists=True))
def dummy_process_something(infile):

    with Path(infile).open('a') as handle:
        handle.write('\n{} Modified by `processSomething {}`.\n'.format(
            get_process_stamp(), infile
        ))


if __name__ == '__main__':
    cli()
