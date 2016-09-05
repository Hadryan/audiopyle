class RemoteFileMeta(object):
    @staticmethod
    def from_dict(remote_file_meta_dict):
        try:
            return RemoteFileMeta(name=remote_file_meta_dict.get("fileName")
                                       or remote_file_meta_dict.get("name"),
                                  size=remote_file_meta_dict.get("size"),
                                  upload_timestamp=remote_file_meta_dict.get("uploadTimestamp")
                                                   or remote_file_meta_dict.get("upload_timestamp"))
        except Exception as e:
            print("Could not decode dict to RemoteFileMeta. Input: {} Details: {}".format(remote_file_meta_dict, e))
            return None

    def __init__(self, name, size, upload_timestamp):
        self.name = name
        self.size = size
        self.upload_timestamp = upload_timestamp

    def __hash__(self):
        return hash((self.name, self.size, self.upload_timestamp))

    def __eq__(self, other):
        return self.name == other.name, self.size == other.size, self.upload_timestamp == other.upload_timestamp

    def __str__(self):
        return "RemoteFileMeta: file name: {}, file size: {}, upload timestamp: {}." \
            .format(self.name, self.size, self.upload_timestamp)

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return self.__dict__
