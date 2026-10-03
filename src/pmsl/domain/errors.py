"""向调用方提供可以区分的失败原因。"""


class PmslError(Exception):
    """可展示给用户的业务错误。"""


class ValidationError(PmslError):
    pass


class UnsafePathError(PmslError):
    pass


class StorageError(PmslError):
    pass


class UnsupportedSchemaError(StorageError):
    pass


class InstanceRunningError(StorageError):
    pass


class MigrationError(PmslError):
    pass


class TaskCancelled(PmslError):
    pass


class DownloadError(PmslError):
    pass


class PreparationError(PmslError):
    pass
