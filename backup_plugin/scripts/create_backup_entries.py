"""
Note this script is specific to Unimus

This script is an example of how to perform the following:create backup db records
    1. Get a list of devices with backups containing a diff within the last 24 hours from Unimus
        2. Per the list of devices, get the last two backups for each.
            3. Create a diff of the last two backups.
            4. Create an HTML rendering of the diff
            5. Add a backup entry containing the device and backup info along with the diff HTML

"""
from extras.scripts import *
import logging
import subprocess
from bs4 import BeautifulSoup

from dcim.models import Device
from backup_plugin.utils import unimus
from backup_plugin.models import Backup

# logging.basicConfig(
#     level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logging.basicConfig()
logger = logging.getLogger(f"backup_plugin.scripts.{__name__}")


def process():
    client = unimus.Client()

    # get list of devices with backup diffs
    data, diff_data = client.get_backups()
    # print(diff_data)
    # print(f"data: {data}")

    errors = []

    for k, v in (diff_data or {}).items():
        logger.info(f"k: {k}, {v.keys()}, {v.get('backups')}")
        if not v.get('backups'):
            raise ValueError(f"No backups found for {k}")

        # use Popen to pass diff to diff2html
        _diff2html = subprocess.Popen([
            'diff2html', '-i', 'stdin', '-s', 'line', '--lm', 'lines', '-o', 'stdout'
        ], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        _diff2html.stdin.write(v.get('diff'))
        _diff2html.stdin.flush()
        _out, _err = _diff2html.communicate()
        _diff2html.wait()

        # use Soup to extract just the diff table
        _soup = BeautifulSoup(_out, 'html.parser')

        # find the results table by class
        _table = _soup.find('table', class_='d2h-diff-table')
        if not _table:
            errors.append(f"{k} No table found")
            continue

        # lookup the device by description
        device = Device.objects.filter(name=k).first()

        # create a record
        Backup(
            name=k, orig_id=v.get('backups')[0]['id'], rev_id=v.get('backups')[1]['id'],
            diff_info=v.get('backups'),
            device_id=getattr(device, 'id', None),
            diff=str(_table)
        ).save()

    return errors


class CreateBackupEntries(Script):
    class Meta:
        name = "create_backup_entries"
        description = "Creates backup entries"

    def run(self, data, commit):
        try:
            self.log_info(f"Processing backups with arguments: {data}")
            errors = process()
            if errors:
                for error in errors:
                    self.log_warning(error)
        except Exception as e:
            logger.exception(f"{e}")
            self.log_failure(f"Error: {e}")


if __name__ == '__main__':
    process()
