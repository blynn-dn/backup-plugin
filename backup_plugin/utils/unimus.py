"""
Utility functions for Unimus

References:
    https://wiki.unimus.net/display/UNPUB/Full+API+v.2+documentation
"""
import base64
import difflib
import logging
from datetime import datetime, timezone, time

import requests
from requests import Request

from netbox.plugins import get_plugin_config

logger = logging.getLogger(f"netbox.plugins.{__name__}")

# get this plugin's config from configuration.py
config = get_plugin_config('backup_plugin', 'unimus')


class Client:
    def __init__(self, base_url: str = None, token: str = None, **kwargs):
        self._base_url = base_url or config['base_url']
        self._token = token or config['token']

        self._session = requests.Session()
        self._session.verify = False
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            'Content-Type': 'application/json'
        }

        self._timeout = kwargs.pop('timeout', None) or (5, 30)

    # region device
    def get_devices(self, page: int = None, size: int = None, attrs: str = None):
        """get devices"""
        params = {}
        if page is not None:
            params['page'] = page
        if size is not None:
            params['size'] = size
        if attrs is not None:
            params['attrs'] = attrs

        return self.execute(f"/devices", params=params)

    def get_device(self, device_id: str):
        """get device info by device_id"""
        return self.execute(f"/devices/{device_id}")

    def get_device_by_name(self, name: str, attrs: str = 's,c'):
        data: dict = self.execute(f"/devices/findByDescription/{name}?attr={attrs}")
        # logger.info(f"data: {data}")
        return data.get('data', [])[0] if data and 'data' in data and data['data'] else {}

    def get_device_latest_backup(self, device_id: str):
        """get device backup by device_id"""
        return self.execute(f"/devices/{device_id}/backups/latest")

    def get_device_latest_backup_diff(self, device_id: str):
        return self._render_diff(self.get_device_backups(device_id, 0, 2) or [])

    def get_device_backups(self, device_id: str, page: int = None, size: int = None):
        """get device backups by device_id"""
        params = {}
        if page is not None:
            params['page'] = page
        if size is not None:
            params['size'] = size
        data = self.execute(f"/devices/{device_id}/backups", params=params)

        return data.get('data', []) if data and 'data' in data else {}

    # endregion

    def _render_diff(self, backups: list):
        """
        Renders a diff between two backups.
        Args:
            backups (list): A list containing the orig and new backups (the last 2 backups)

        Returns:
            (dict): A dictionary containing the backup meta/details and unified diff string
        """
        # get the last 2
        diff_data = {'backups': [], 'diff': None}
        for info in backups or []:
            logger.info(f"info: {info.keys()}")
            diff_data['backups'].append({
                'id': info['id'],
                'valid_since': datetime.fromtimestamp(
                    info['validSince'], tz=timezone.utc).isoformat() if info.get('validSince') else None,
                'valid_until': datetime.fromtimestamp(
                    info['validUntil'], tz=timezone.utc).isoformat() if info.get('validUntil') else None,
                'config': self.decode(info['bytes'])
            })

        if len(diff_data['backups']) > 1:
            # may not need the backup diff
            # diff_info = client.get_backup_diff(backup_data[0]['id'], backup_data[1]['id'])

            # create a unified diff -- note `lineterm=''` and join with `\n` -- this handles formatting
            # that is friendly with the javascript Diff2HtmlUI
            # note that the most recent backup (newest) is element 0 whereas the prior (old) is element 1
            # therefore the older should be on the left (as the first param) and the newer should be on the right
            # (as the 2nd param)
            diff_data['diff'] = '\n'.join(list(difflib.unified_diff(
                diff_data['backups'][1]['config'].splitlines(),
                diff_data['backups'][0]['config'].splitlines(),
                fromfile=str(diff_data['backups'][1]['id']),
                tofile=str(diff_data['backups'][0]['id']),
                lineterm=''
            )))

        return diff_data

    def get_backups(self, since: int | None = None, until: int | None = None, limit: int | None = None):
        """
        Get all backups within `since` and `until, exclusive.

        All dates are UTC.

        Args:
            since(int|None): Unix Epoch start time (defaults to current day at midnight)
            until(int): Unix Epoch end time (defaults to end of current day)
            limit (int): Limit the number of backups to process. This is primarily limit processing for testing.

        Returns:
            ((dict), (list), (dict)): list of process_info, backups and relate diff_data dicts
        """
        logger.info(f"-> {since}, {until}, {limit}")
        if not since:
            since = int(datetime.combine(datetime.now(), time.min).timestamp())
        elif isinstance(since, int) and since < 1:
            raise ValueError(f"parameter 'since' must be a positive integer, got {type(since)}")
        elif isinstance(since, datetime):
            since = int(since.timestamp())

        if not until:
            until = int(datetime.combine(datetime.now(), time.max).timestamp())
        elif isinstance(until, int) and until < since:
            raise ValueError(f"parameter 'until' must be a positive integer and > 'since', got {type(since)}")
        elif isinstance(until, datetime):
            until = int(until.timestamp())

        _start = datetime.fromtimestamp(since, tz=timezone.utc)
        _end = datetime.fromtimestamp(until, tz=timezone.utc)
        process_info = {
            "since": since, "until": until, "limit": limit, "start": _start.isoformat(), "end": _end.isoformat()
        }

        logger.info(f"-> {process_info}")

        diff_data = {}
        _params = {'since': since, 'until': until}
        if limit:
            _params.update({'size': limit, 'page': 0})

        data: dict = self.execute('devices/findByChangedBackup', params=_params) or []
        for backup in data.get('data', {}):

            description = backup.get('description') or f"{backup.get('address')} - {backup.get('model')}"
            diff_data[description] = backup
            diff_data[description]['backups'] = []

            # get the last 2 backups and render the diff
            diff_data[description].update(
                self._render_diff(self.get_device_backups(backup['id'], 0, 2) or []))

            '''
            # get the last 2
            backup_data = []
            for info in self.get_device_backups(backup['id'], 0, 2) or []:
                logger.info(f"info: {info.keys()}")
                diff_data[description]['backups'].append({
                    'id': info['id'],
                    'valid_since': datetime.fromtimestamp(
                        info['validSince'], tz=timezone.utc).isoformat() if info.get('validSince') else None,
                    'valid_until': datetime.fromtimestamp(
                        info['validUntil'], tz=timezone.utc).isoformat() if info.get('validUntil') else None,
                })
                backup_data.append({
                    'id': info['id'],
                    'config': self.decode(info['bytes'])
                })

            if len(backup_data) > 1:
                # may not need the backup diff
                # diff_info = client.get_backup_diff(backup_data[0]['id'], backup_data[1]['id'])

                # create a unified diff -- note `lineterm=''` and join with `\n` -- this handles formatting
                # that is friendly with the javascript Diff2HtmlUI
                # note that the most recent backup (newest) is element 0 whereas the prior (old) is element 1
                # therefore the older should be on the left (as the first param) and the newer should be on the right
                # (as the 2nd param)
                diff_data[description]['diff'] = '\n'.join(list(difflib.unified_diff(
                    backup_data[1]['config'].splitlines(),
                    backup_data[0]['config'].splitlines(),
                    fromfile=str(backup_data[1]['id']),
                    tofile=str(backup_data[0]['id']),
                    lineterm=''
                )))

            else:
                diff_data[description]['diff'] = None
            '''

        return process_info, data, diff_data

    def get_backup_diff(self, orig_id: str, rev_id: str):
        return self.execute(f"/backups/diff?origId={orig_id}&revId={rev_id}")

    @staticmethod
    def decode(data: str):
        """helper: decode a base64 encoded string"""
        return base64.b64decode(data).decode('utf-8')

    def execute(self, ep: str, method: str = 'get', **kwargs):
        """
        Calls the API with a given Verb, endpoint, etc.
        Args:
            ep: (str) The endpoint to call
            method: (str) A method verb such as "get", "post", "put" (default to "get")
            **kwargs:
                success_response_code (int): defaults to 200
                data (dict): data/payload for post or put

                Potential args to add:
                #retries (int): optional number of attempts (defaults to 0 retries)
                #backoff_factor (float): optional delay in seconds between retries (defaults to 0.3)
                #api_version (str): optional api_version (defaults to 'v1')
                #status_forcelist: (iterable) A set of integer HTTP status codes that we should force a retry on.
                #method_whitelist: (iterable) Set of upper-cased HTTP method verbs that we should retry on.

        Returns:
            (List[Dict] | str)
        """
        _data = kwargs.pop('data', None)
        _params = kwargs.pop('params', None)
        _success_response_code = kwargs.pop('success_response_code', 200)

        # create a prepared request
        _prepared_req = Request(
            method,
            f"{self._base_url}{ep}",
            params=_params,
            headers=self._headers,
            json=_data if _data else None
        ).prepare()

        logger.info(f"request: {_prepared_req.method} {_prepared_req.url}")

        # remove 500 from default retry list as CG returns a 500
        response = self._session.send(_prepared_req, timeout=self._timeout)
        response.raise_for_status()

        if 'application/json' in response.headers.get('Content-Type', ''):
            # if the response is json
            return response.json()
        return response.text

