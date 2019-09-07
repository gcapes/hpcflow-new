"""`hpcflow.scheduler.py`"""

from datetime import datetime

from hpcflow import CONFIG, FILE_NAMES
from hpcflow._version import __version__


class Scheduler(object):

    options = None
    output_dir = None
    error_dir = None

    def __repr__(self):
        out = ('{}('
               'options={!r}, '
               'output_dir={!r}, '
               'error_dir={!r}'
               ')').format(
            self.__class__.__name__,
            self.options,
            self.output_dir,
            self.error_dir,
        )
        return out


class SunGridEngine(Scheduler):

    _NAME = 'sge'
    SHEBANG = '#!/bin/bash --login'

    # Options that determine how to set the output/error directories:
    STDOUT_OPT = 'o'
    STDERR_OPT = 'e'
    STDOUT_OPT_FMT = '{}/'
    STDERR_OPT_FMT = '{}/'

    # Required options to ensure the job scripts work with hpcflow:
    REQ_OPT = ['cwd']
    REQ_PARAMETRISED_OPT = {}

    ALLOWED_USER_OPTS = [
        'pe',       # Parallel environment
        'l',        # Resource request
        'tc',       # Max running tasks
    ]

    def __init__(self, options=None, output_dir=None, error_dir=None):

        for i in options:
            if i not in SunGridEngine.ALLOWED_USER_OPTS:
                msg = ('Option "{}" is not allowed for scheduler "{}". Allowed options '
                       'are: {}.')
                raise ValueError(
                    msg.format(i, SunGridEngine._NAME, SunGridEngine.ALLOWED_USER_OPTS))

        self.output_dir = output_dir or CONFIG['default_output_dir']
        self.error_dir = error_dir or CONFIG['default_error_dir']
        self.options = options

    def get_formatted_options(self, max_num_tasks, task_step_size):

        opts = ['#$ -{}'.format(i) for i in SunGridEngine.REQ_OPT]
        opts.append('#$ -{} {}'.format(
            SunGridEngine.STDOUT_OPT,
            SunGridEngine.STDOUT_OPT_FMT.format(self.output_dir)),
        )
        opts.append('#$ -{} {}'.format(
            SunGridEngine.STDERR_OPT,
            SunGridEngine.STDERR_OPT_FMT.format(self.error_dir)),
        )
        opts += ['#$ -{} {}'.format(i, j)
                 for i, j in SunGridEngine.REQ_PARAMETRISED_OPT.items()]
        opts += ['#$ -{} {}'.format(k, v).strip()
                 for k, v in sorted(self.options.items())]
        opts += ['', '#$ -t 1-{}:{}'.format(max_num_tasks, task_step_size)]

        return opts

    def write_jobscript(self, dir_path, workflow_directory, command_group_order,
                        max_num_tasks, task_step_size, modules, archive,
                        alternate_scratch_dir, command_group_submission_id):
        """Write the jobscript.

        Parameters
        ----------
        archive : bool

        """

        js_ext = CONFIG.get('jobscript_ext', '')
        js_name = 'js_{}'.format(command_group_order)
        js_fn = js_name + js_ext
        js_path = dir_path.joinpath(js_fn)

        cmd_name = 'cmd_{}'.format(command_group_order)
        cmd_fn = cmd_name + js_ext

        submit_dir_relative = dir_path.relative_to(workflow_directory).as_posix()

        wk_dirs_path = ('${{ITER_DIR}}/working_dirs_{}{}').format(
            command_group_order, CONFIG['working_dirs_file_ext'])

        dt_stamp = datetime.now().strftime(r'%Y.%m.%d at %H:%M:%S')
        about_msg = ['# --- jobscript generated by `hpcflow` (version: {}) '
                     'on {} ---'.format(__version__, dt_stamp)]

        define_dirs_A = [
            'ROOT_DIR=`pwd`',
            'SUBMIT_DIR=$ROOT_DIR/{}'.format(submit_dir_relative),
            'ITER_DIR=$SUBMIT_DIR/iter_$ITER_IDX',
            'LOG_PATH=$ITER_DIR/log_{}.$SGE_TASK_ID'.format(command_group_order),
            'TASK_IDX=$((($SGE_TASK_ID - 1)/{}))'.format(task_step_size),
        ]

        write_cmd_exec = [('hpcflow write-runtime-files -d $ROOT_DIR {} $TASK_IDX '
                           '$ITER_IDX > $LOG_PATH 2>&1').format(
                               command_group_submission_id)]

        define_dirs_B = [
            'INPUTS_DIR_REL=`sed -n "${{SGE_TASK_ID}}p" {}`'.format(wk_dirs_path),
            'INPUTS_DIR=$ROOT_DIR/$INPUTS_DIR_REL',
        ]

        if alternate_scratch_dir:
            alt_scratch_exc_path = '$ITER_DIR/{}_{}_$TASK_IDX{}'.format(
                FILE_NAMES['alt_scratch_exc_file'],
                command_group_order,
                FILE_NAMES['alt_scratch_exc_file_ext'],
            )
            define_dirs_B.append('ALT_SCRATCH_EXC=' + alt_scratch_exc_path)
            in_dir_scratch = 'INPUTS_DIR_SCRATCH={}/$INPUTS_DIR_REL'.format(
                alternate_scratch_dir)
            copy_to_alt = [
                ('rsync -avviz --exclude-from="${ALT_SCRATCH_EXC}" '
                 '$INPUTS_DIR/ $INPUTS_DIR_SCRATCH >> $LOG_PATH 2>&1'),
                '',
            ]
            move_from_alt = [
                '',
                ('rsync -avviz $INPUTS_DIR_SCRATCH/ $INPUTS_DIR --remove-source-files'
                 ' >> $LOG_PATH 2>&1'),
                '',
            ]
        else:
            in_dir_scratch = 'INPUTS_DIR_SCRATCH=$INPUTS_DIR'
            copy_to_alt = []
            move_from_alt = []

        define_dirs_B.append(in_dir_scratch)

        log_stuff = [
            r'printf "Jobscript variables:\n" >> $LOG_PATH 2>&1',
            r'printf "ITER_IDX:\t ${ITER_IDX}\n" >> $LOG_PATH 2>&1',
            r'printf "ROOT_DIR:\t ${ROOT_DIR}\n" >> $LOG_PATH 2>&1',
            r'printf "SUBMIT_DIR:\t ${SUBMIT_DIR}\n" >> $LOG_PATH 2>&1',
            r'printf "ITER_DIR:\t ${ITER_DIR}\n" >> $LOG_PATH 2>&1',
            r'printf "LOG_PATH:\t ${LOG_PATH}\n" >> $LOG_PATH 2>&1',
            r'printf "SGE_TASK_ID:\t ${SGE_TASK_ID}\n" >> $LOG_PATH 2>&1',
            r'printf "TASK_IDX:\t ${TASK_IDX}\n" >> $LOG_PATH 2>&1',
            r'printf "INPUTS_DIR_REL:\t ${INPUTS_DIR_REL}\n" >> $LOG_PATH 2>&1',
            r'printf "INPUTS_DIR:\t ${INPUTS_DIR}\n" >> $LOG_PATH 2>&1',
            r'printf "INPUTS_DIR_SCRATCH:\t ${INPUTS_DIR_SCRATCH}\n" >> $LOG_PATH 2>&1',
        ]

        if alternate_scratch_dir:
            log_stuff.append(
                r'printf "ALT_SCRATCH_EXC:\t ${ALT_SCRATCH_EXC}\n" >> $LOG_PATH 2>&1',
            )

        log_stuff.append(r'printf "\n" >> $LOG_PATH 2>&1')

        if modules:
            loads = [''] + ['module load {}'.format(i) for i in sorted(modules)] + ['']
        else:
            loads = []

        set_task_args = '-d $ROOT_DIR {} $TASK_IDX $ITER_IDX >> $LOG_PATH 2>&1'.format(
            command_group_submission_id)
        cmd_exec = [
            'hpcflow set-task-start {}'.format(set_task_args),
            '',
            'cd $INPUTS_DIR_SCRATCH',
            '. $SUBMIT_DIR/{}'.format(cmd_fn),
            '',
            'hpcflow set-task-end {}'.format(set_task_args),
        ]

        arch_lns = []
        if archive:
            arch_lns = [
                ('hpcflow archive -d $ROOT_DIR {} $TASK_IDX $ITER_IDX >> '
                 '$LOG_PATH 2>&1'.format(command_group_submission_id)),
                ''
            ]

        js_lines = ([SunGridEngine.SHEBANG, ''] +
                    about_msg + [''] +
                    self.get_formatted_options(max_num_tasks, task_step_size) + [''] +
                    define_dirs_A + [''] +
                    write_cmd_exec + [''] +
                    define_dirs_B + [''] +
                    log_stuff + [''] +
                    loads + [''] +
                    copy_to_alt +
                    cmd_exec +
                    move_from_alt +
                    arch_lns)

        # Write jobscript:
        with js_path.open('w') as handle:
            handle.write('\n'.join(js_lines))

        return js_path


class DirectExecution(Scheduler):
    pass
