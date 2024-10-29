import os
import sys
import subprocess
import plistlib
from datetime import datetime


def schedule_task(execute_datetime: datetime):
    """
    Schedules task_executor to run at the date and time provided using macOS launchd.
    :param execute_datetime: A DateTime object representing when to schedule the next run.
    """
    python_path = sys.executable
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'main.py')

    label = f'com.life_manager.execute'
    plist_path = os.path.expanduser(f'~/Library/LaunchAgents/{label}.plist')

    if os.path.exists(plist_path):
        os.system(f'launchctl unload {plist_path}')

    start_calendar_interval = {
            'Year': execute_datetime.year,
            'Month': execute_datetime.month,
            'Day': execute_datetime.day,
            'Hour': execute_datetime.hour,
            'Minute': execute_datetime.minute
        }

    plist = {
        'Label': label,
        'ProgramArguments': [python_path, script_path],
        'StartCalendarInterval': start_calendar_interval,
        'RunAtLoad': False,
        'KeepAlive': False
    }

    with open(plist_path, 'wb') as f:
        plistlib.dump(plist, f)

    result = subprocess.run(['launchctl', 'load', plist_path], capture_output=True, text=True)
    if result.returncode != 0:
        print(f'Error loading job: {result.stderr}')
    else:
        print(f'Successfully scheduled task at {execute_datetime}')
