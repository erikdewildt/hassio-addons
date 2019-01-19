import json
import logging
import os
import sys
from json import JSONDecodeError

import dropbox
import requests

logger = logging.getLogger('dropbox_backup')
logger.setLevel(logging.DEBUG)
log_console = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)-8s - %(message)s')
log_console.setFormatter(formatter)
logger.addHandler(log_console)


class DropboxAPI:
    """Simple DropBox API Wrapper."""

    CHUNK_SIZE = 4 * 1024 * 1024

    def __init__(self, token):
        """
        Initialise Dropbox API.

        :param token: The DropBox oauth token
        """
        self.dbx = dropbox.Dropbox(token)

        try:
            dropbox_account = self.dbx.users_get_current_account()
        except dropbox.exceptions.AuthError as error:
            logger.error('Error logging into DropBox, please check token.')
            logger.debug(error)
            sys.exit(1)

        logger.info(f'Logged in to DropBox as user: {dropbox_account.email}')

    def show_dropbox_usage(self):
        """Log DropBox usage statistics."""
        space_usage = self.dbx.users_get_space_usage()
        used_space = int(space_usage.used / 10 ** 6)
        allocated_space = int(space_usage.allocation.get_individual().allocated / 10 ** 6)
        percentage_used = int((100 * used_space) / allocated_space)
        logger.info(f'DropBox usage: {used_space} Mb / {allocated_space} Mb (Usage: {percentage_used}%)')

    def upload(self, destination_path, source_path):
        """
        Upload a file to DropBox.

        :param destination_path: The path to the destination file.
        :param source_path: The path to the source file.
        """
        result = None
        destination_path = os.path.join(destination_path, source_path.split('/')[-1])
        file_size = os.path.getsize(source_path)

        try:
            if os.path.exists(source_path) and file_size > 0:
                with open(source_path, 'rb') as file:
                    if file_size <= self.CHUNK_SIZE:
                        result = self.dbx.files_upload(f=file.read(), path=destination_path)
                    else:
                        upload_session_start_result = self.dbx.files_upload_session_start(file.read(self.CHUNK_SIZE))
                        cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                                   offset=file.tell())
                        commit = dropbox.files.CommitInfo(path=destination_path)

                        while file.tell() < file_size:
                            if (file_size - file.tell()) <= self.CHUNK_SIZE:
                                result = self.dbx.files_upload_session_finish(file.read(self.CHUNK_SIZE), cursor,
                                                                              commit)
                            else:
                                self.dbx.files_upload_session_append_v2(file.read(self.CHUNK_SIZE), cursor)
                                cursor.offset = file.tell()
                                progress = (file.tell() * 100) / file_size
                                logger.info(f'Uploading `{file.name}`, progress: {progress:.0f} %')

        except (dropbox.exceptions.HttpError, dropbox.exceptions.ApiError) as error:
            logger.error(f'Error while uploading `{destination_path}` to DropBox.')
            logger.debug(f'Error: {error}')

        if result:
            logger.info(f'Uploaded `{result.name}` (Size: {result.size / 10 ** 6:.2f} Mb)')

    def delete(self, path):
        """
        Delete a file from DropBox.

        :param path: The path to the file to be deleted.
        """
        results = []

        try:
            results.append(self.dbx.files_delete_v2(path))
        except dropbox.exceptions.ApiError as error:
            logger.error(f'Error deleting file `{path}` from DropBox.')
            logger.debug(f'Error: {error}')

        if len(results) > 0:
            for result in results:
                logger.info(f'Deleted `{result.metadata.name}` from DropBox. '
                            f'(Size: {result.metadata.size / 10 ** 6:.2f} Mb)')

    def list_files(self, path):
        """
        Return a list of files ordered by date.

        :param path: The path for which files need to be listed.
        :return: A sorted by date list of file maps.
        """
        files = []

        try:
            for file in self.dbx.files_list_folder(path).entries:
                files.append({'name': file.name,
                              'date': file.client_modified,
                              'size': file.size,
                              'path': file.path_lower})
        except (AttributeError, dropbox.exceptions.ApiError) as error:
            logger.error('Error listing files on DropBox, please check path setting.')
            logger.debug(f'Error: {error}')

        return sorted(files, key=lambda item: item['date'], reverse=True)

    def keep_last(self, path, number_to_keep):
        """
        Keep the last x file in the specified DropBox folder.

        :param path: Path for which files need to be checked.
        :param number_to_keep: The number of files to keep
        """
        files = self.list_files(path)
        number_to_remove = len(files) - number_to_keep
        if number_to_remove > 0:
            files_to_remove = files[-number_to_remove:]

            if len(files_to_remove) > 0:
                logger.info(f'Keeping last {number_to_keep} remote backups will remove {len(files_to_remove)} files.')
            for file in files_to_remove:
                self.delete(file['path'])
        else:
            logger.info(f'Keeping last {number_to_keep} remote backups, no need to remove any.')


class DropboxBackup:
    """DropBox Backup."""

    BASE_URL = "http://hassio/"
    BACKUP_PATH = "/backup/"
    HEADERS = {'X-HASSIO-KEY': os.environ.get('HASSIO_TOKEN')}

    def __init__(self):
        """Initialisation of the DropboxBackup."""

        try:
            with open('/data/options.json') as options_file:
                try:
                    self.options = json.loads(options_file.read())
                except JSONDecodeError as error:
                    logger.warning('Could not parse options due to error.')
                    logger.debug(f'Error: {error}')
                    sys.exit(1)
        except FileNotFoundError as error:
            logger.error(f'Options file not found, not running inside HassIO?')
            logger.debug(f'Error: {error}')
            sys.exit(1)

        self.dropbox = DropboxAPI(self.options['oauth_access_token'])
        self.dropbox.show_dropbox_usage()
        self.sanitize_options()
        self.run()

    def sanitize_options(self):
        """
        Sanitize options

        This will try to make integers from some options in case a string was entered.
        """
        try:
            self.options['number_to_keep_local'] = int(self.options.get('number_to_keep_local'))
            self.options['number_to_keep_remote'] = int(self.options.get('number_to_keep_remote'))
            self.options['remote_path'] = self.options.get('remote_path').rstrip('/')
        except (AttributeError, ValueError) as error:
            logger.error('Error in options, please check your config.')
            logger.debug(f'Error: {error}')

    def run(self):
        """Main loop waiting for commands..."""
        while True:
            with open('/dev/stdin') as stdin:
                stdin_input = stdin.readline()
                stdin.close()

            if stdin_input:
                self.handle_input(stdin_input)

    def handle_input(self, stdin_input):
        """Handle a input command."""
        try:
            input_dict = json.loads(stdin_input)
        except JSONDecodeError as error:
            logger.error(f'No valid JSON payload received')
            logger.debug(f'Error: {error}')
            return False

        if isinstance(input_dict, dict) and str(input_dict.get('command')).lower() == 'sync':
            backup_files = None

            # DropBox
            self.dropbox.show_dropbox_usage()

            try:
                backup_files = [file for file in os.listdir(self.BACKUP_PATH) if
                                os.path.isfile(os.path.join(self.BACKUP_PATH, file))]
            except FileNotFoundError as error:
                logger.error('Error listing files, please check your config.')
                logger.debug(f'Error: {error}')

            remote_files = [file['name'] for file in self.dropbox.list_files(path=self.options['remote_path'])]
            files_to_upload = [file for file in backup_files if file not in remote_files]

            logger.info(f'Need to sync {len(files_to_upload)} file(s).')

            for file in files_to_upload:
                source_path = os.path.join(self.BACKUP_PATH, file)
                self.dropbox.upload(destination_path=self.options['remote_path'], source_path=source_path)

            self.dropbox.keep_last(path=self.options['remote_path'].rstrip('/'),
                                   number_to_keep=self.options['number_to_keep_remote'])

            self.dropbox.show_dropbox_usage()

            # Local
            self.keep_last(number_to_keep=self.options['number_to_keep_local'])
        else:
            logger.info('Wrong input, send `{"command": "sync"}` to trigger backup.')

    def keep_last(self, number_to_keep):
        """
        Keep the last x number of snapshots.

        :param number_to_keep: The number of snapshots to keep.
        """

        snapshot_info = requests.get(f'{self.BASE_URL}snapshots', headers=self.HEADERS)
        snapshot_info.raise_for_status()
        snapshots = sorted(snapshot_info.json()['data']['snapshots'], key=lambda item: item['date'], reverse=True)

        number_to_remove = len(snapshots) - number_to_keep
        if number_to_remove > 0:
            snapshots_to_remove = snapshots[-number_to_remove:]

            if len(snapshots_to_remove) > 0:
                logger.info(f'Keeping last {number_to_keep} local backups will remove '
                            f'{len(snapshots_to_remove)} files.')

            for snapshot in snapshots_to_remove:
                self.delete_snapshot(slug=snapshot['slug'])
        else:
            logger.info(f'Keeping last {number_to_keep} local backups, no need to remove any.')

    def delete_snapshot(self, slug):
        """
        Delete a snapshot.

        :param slug: The `slug` of the snapshot to remove.
        """
        result = requests.post(self.BASE_URL + "snapshots/" + slug + "/remove", headers=self.HEADERS)
        if result.ok:
            logger.info(f'Deleted snapshot `{slug}`')
        else:
            logger.error(f'Error deleting snapshot `{slug}`.')
            logger.debug(f'Error: res.status_code')


if __name__ == '__main__':
    DropboxBackup()
