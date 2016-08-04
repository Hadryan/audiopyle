class RemoteFileMeta(object):
    @staticmethod
    def from_dict(remote_file_meta_dict):
        return RemoteFileMeta(name=remote_file_meta_dict["fileName"],
                              size=remote_file_meta_dict["size"],
                              upload_timestamp=remote_file_meta_dict["uploadTimestamp"])

    def __init__(self, name, size, upload_timestamp):
        self.name = name
        self.size = size
        self.upload_timestamp = upload_timestamp

    def __str__(self):
        return "RemoteFileMeta: file name: {}, file size: {}, upload timestamp: {}."\
            .format(self.name, self.size, self.upload_timestamp)

    def __repr__(self):
        return self.__str__()