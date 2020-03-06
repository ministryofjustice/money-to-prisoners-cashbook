#!/usr/bin/env python

if __name__ == '__main__':
    import os
    import sys

    if sys.version_info[0:2] < (3, 6):
        raise SystemExit('python 3.6+ is required')

    try:
        import mtp_common

        if mtp_common.VERSION < (10,):
            raise ImportError
    except ImportError:
        import pkg_resources

        print('Pre-installing MTP-common')
        pip = pkg_resources.load_entry_point('pip', 'console_scripts', 'pip')
        pip(['--quiet', 'install', '--upgrade', 'money-to-prisoners-common>=10'])

    from mtp_common.build_tasks.executor import Executor

    root_path = os.path.abspath(os.path.dirname(__file__))
    exit(Executor(root_path=root_path).run())
