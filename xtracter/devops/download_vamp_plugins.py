#!/usr/bin/env python
import os

from b2.api import B2Api
from b2.download_dest import DownloadDestLocalFile
from b2.progress import make_progress_listener

# -------------------------- CONFIG --------------------------
REALM = 'production'
ACCOUNT_ID = 'a56c121eaece'
APPLICATION_KEY = '001de304a2f988ad8266285ebbfcebe6aed90717b7'
VAMP_PLUGINS_BUCKET_NAME = 'vamp-plugins'
PLATFORM_DIR = "linux_x64"
DESTINATION = "../resources/vamp_plugins/"


# -------------------------- HELPER FUCNTIONS --------------------------
def _authorize():
    print('Attempting to connect to backblaze...')
    b2api = B2Api()
    b2api.authorize_account(REALM, ACCOUNT_ID, APPLICATION_KEY)
    print('Authorization completed!')
    return b2api


def _retrieve_bucket(b2_api):
    bucket = b2_api.get_bucket_by_name(VAMP_PLUGINS_BUCKET_NAME)
    print('Connected to bucket: {} successfully!'.format(bucket.name))
    return bucket


def _retrieve_platform_remote_file_paths(bucket):
    file_infos = bucket.list_file_names().get('files')
    file_paths = [file_info.get('fileName') for file_info in file_infos]
    platform_specific_remote_files_paths = filter(lambda filename: filename.startswith(PLATFORM_DIR), file_paths)
    print('Selected platform specific file paths.')
    return platform_specific_remote_files_paths


def download_remote_files_to(bucket, local_dest_dir):
    print('Downloading {} files to folder: {}'.format(len(remote_file_paths), local_dest_dir))
    for remote_file_path in remote_file_paths:
        file_name = remote_file_path.split('/')[-1]
        if not file_name.startswith('.'):
            destination_file_path = os.path.join(local_dest_dir, file_name)
            if os.path.exists(destination_file_path):
                print('Skipping already existing file: {}'.format(destination_file_path))
            else:
                print('Downloading remote file: {} to: {}'.format(remote_file_path, destination_file_path))
                destination_object = DownloadDestLocalFile(destination_file_path,
                                                           make_progress_listener(destination_file_path, True))
                bucket.download_file_by_name(remote_file_path, destination_object)
        else:
            print('Skipping hidden file: {}'.format(file_name))
    print('Download completed.')


def get_local_destination_dir():
    return os.path.abspath(DESTINATION)


# -------------------------- PROCEDURE --------------------------
api = _authorize()
b2_bucket = _retrieve_bucket(api)
remote_file_paths = _retrieve_platform_remote_file_paths(b2_bucket)
destination_dir = get_local_destination_dir()
download_remote_files_to(b2_bucket, destination_dir)