import json
from core.exceptions import Error, RequestDataError

class Driver(object):
    def __init__(self, storage):
        self.storage = storage

    def add_disk(self):
        mappings = self.storage.get_mappings()
        if len(mappings) == 0:
            raise Error("No mappings found.")
        cmd = [
            "array", "add", "disk",
            "-a", self.storage.request_data["array"]["array_name"],
            "--name", self.storage.disk_name(),
            "--size", self.storage.request_data["size"]
        ] + mappings
        ret = self.storage.proxy_action(" ".join(cmd))
        try:
            data = json.loads(ret["data"][0]["stdout"])
            return data
        except ValueError:
            Error("unexpected add disk output format: %s" % ret)

    def resize_disk(self):
        if "disk_devid" not in self.storage.request_data:
            raise RequestDataError("The 'disk_devid' key is mandatory in request data")
        cmd = [
            "array", "resize", "tdev",
            "-a", self.storage.request_data["array"]["array_name"],
            "--dev", self.storage.request_data["disk_devid"],
            "--size", self.storage.request_data["size"]
        ]
        ret = self.storage.proxy_action(" ".join(cmd))

    def del_disk(self):
        if "disk_devid" not in self.storage.request_data:
            raise RequestDataError("The 'disk_devid' key is mandatory in request data")
        cmd = [
            "array", "del", "disk",
            "-a", self.storage.request_data["array"]["array_name"],
            "--dev", self.storage.request_data["disk_devid"]
        ]
        ret = self.storage.proxy_action(" ".join(cmd))


