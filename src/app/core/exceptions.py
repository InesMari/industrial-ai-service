
class AppException(Exception):
    def __init__(self, code: str,message: str, status_code: int = 400):
        self.code = code
        self.status_code = status_code
        self.message = message

class DeviceOfflineError(AppException):
    def __init__(self, device_id: str):
        super().__init__(
            code="DEVICE_OFFLINE",
            message=f"设备 {device_id} 离线",
            status_code=503,
        )

class InvalidParameterError(AppException):
    def __init__(self, message: str):
        super().__init__(code="INVALID_PARAMETER", message=message, status_code=400)