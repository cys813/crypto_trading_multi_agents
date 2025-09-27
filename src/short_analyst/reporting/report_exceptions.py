"""
报告生成异常处理

该模块定义了报告生成过程中可能出现的各种异常类型。
"""


class ReportError(Exception):
    """报告基础异常类"""
    pass


class ReportGenerationError(ReportError):
    """报告生成错误"""
    def __init__(self, message: str, error_code: str = None, original_error: Exception = None):
        super().__init__(message)
        self.error_code = error_code
        self.original_error = original_error

    def __str__(self):
        error_msg = super().__str__()
        if self.error_code:
            error_msg = f"[{self.error_code}] {error_msg}"
        if self.original_error:
            error_msg += f" (原始错误: {str(self.original_error)})"
        return error_msg


class ReportValidationError(ReportError):
    """报告验证错误"""
    def __init__(self, message: str, field_name: str = None, validation_errors: list = None):
        super().__init__(message)
        self.field_name = field_name
        self.validation_errors = validation_errors or []

    def __str__(self):
        error_msg = super().__str__()
        if self.field_name:
            error_msg = f"字段 '{self.field_name}': {error_msg}"
        if self.validation_errors:
            error_msg += f" (验证错误: {', '.join(self.validation_errors)})"
        return error_msg


class ReportExportError(ReportError):
    """报告导出错误"""
    def __init__(self, message: str, export_format: str = None, file_path: str = None):
        super().__init__(message)
        self.export_format = export_format
        self.file_path = file_path

    def __str__(self):
        error_msg = super().__str__()
        if self.export_format:
            error_msg = f"{self.export_format} 导出错误: {error_msg}"
        if self.file_path:
            error_msg += f" (文件: {self.file_path})"
        return error_msg


class ChartGenerationError(ReportError):
    """图表生成错误"""
    def __init__(self, message: str, chart_type: str = None, chart_id: str = None):
        super().__init__(message)
        self.chart_type = chart_type
        self.chart_id = chart_id

    def __str__(self):
        error_msg = super().__str__()
        if self.chart_type:
            error_msg = f"{self.chart_type} 图表错误: {error_msg}"
        if self.chart_id:
            error_msg += f" (图表ID: {self.chart_id})"
        return error_msg


class DataProcessingError(ReportError):
    """数据处理错误"""
    def __init__(self, message: str, data_source: str = None, processing_step: str = None):
        super().__init__(message)
        self.data_source = data_source
        self.processing_step = processing_step

    def __str__(self):
        error_msg = super().__str__()
        if self.data_source:
            error_msg = f"数据源 '{self.data_source}': {error_msg}"
        if self.processing_step:
            error_msg += f" (处理步骤: {self.processing_step})"
        return error_msg


class TemplateError(ReportError):
    """模板错误"""
    def __init__(self, message: str, template_id: str = None, template_name: str = None):
        super().__init__(message)
        self.template_id = template_id
        self.template_name = template_name

    def __str__(self):
        error_msg = super().__str__()
        if self.template_id:
            error_msg = f"模板ID '{self.template_id}': {error_msg}"
        if self.template_name:
            error_msg += f" (模板名: {self.template_name})"
        return error_msg


class ConfigurationError(ReportError):
    """配置错误"""
    def __init__(self, message: str, config_key: str = None, config_value: str = None):
        super().__init__(message)
        self.config_key = config_key
        self.config_value = config_value

    def __str__(self):
        error_msg = super().__str__()
        if self.config_key:
            error_msg = f"配置项 '{self.config_key}': {error_msg}"
        if self.config_value:
            error_msg += f" (值: {self.config_value})"
        return error_msg


class InsufficientDataError(ReportError):
    """数据不足错误"""
    def __init__(self, message: str, required_count: int = None, available_count: int = None):
        super().__init__(message)
        self.required_count = required_count
        self.available_count = available_count

    def __str__(self):
        error_msg = super().__str__()
        if self.required_count is not None and self.available_count is not None:
            error_msg += f" (需要: {self.required_count}, 可用: {self.available_count})"
        return error_msg


class UnsupportedFormatError(ReportError):
    """不支持格式错误"""
    def __init__(self, message: str, requested_format: str = None, supported_formats: list = None):
        super().__init__(message)
        self.requested_format = requested_format
        self.supported_formats = supported_formats or []

    def __str__(self):
        error_msg = super().__str__()
        if self.requested_format:
            error_msg = f"不支持的格式 '{self.requested_format}': {error_msg}"
        if self.supported_formats:
            error_msg += f" (支持的格式: {', '.join(self.supported_formats)})"
        return error_msg


class FileAccessError(ReportError):
    """文件访问错误"""
    def __init__(self, message: str, file_path: str = None, operation: str = None):
        super().__init__(message)
        self.file_path = file_path
        self.operation = operation

    def __str__(self):
        error_msg = super().__str__()
        if self.file_path:
            error_msg = f"文件 '{self.file_path}': {error_msg}"
        if self.operation:
            error_msg += f" (操作: {self.operation})"
        return error_msg


class NetworkError(ReportError):
    """网络错误"""
    def __init__(self, message: str, url: str = None, status_code: int = None):
        super().__init__(message)
        self.url = url
        self.status_code = status_code

    def __str__(self):
        error_msg = super().__str__()
        if self.url:
            error_msg = f"URL '{self.url}': {error_msg}"
        if self.status_code:
            error_msg += f" (状态码: {self.status_code})"
        return error_msg


class TimeoutError(ReportError):
    """超时错误"""
    def __init__(self, message: str, timeout_seconds: float = None, operation: str = None):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds
        self.operation = operation

    def __str__(self):
        error_msg = super().__str__()
        if self.timeout_seconds:
            error_msg = f"超时 ({self.timeout_seconds}秒): {error_msg}"
        if self.operation:
            error_msg += f" (操作: {self.operation})"
        return error_msg


class MemoryError(ReportError):
    """内存错误"""
    def __init__(self, message: str, required_memory: int = None, available_memory: int = None):
        super().__init__(message)
        self.required_memory = required_memory
        self.available_memory = available_memory

    def __str__(self):
        error_msg = super().__str__()
        if self.required_memory is not None and self.available_memory is not None:
            error_msg += f" (需要: {self.required_memory}MB, 可用: {self.available_memory}MB)"
        return error_msg


# 错误码定义
class ErrorCodes:
    """错误码定义"""
    # 报告生成错误 (1000-1999)
    REPORT_GENERATION_FAILED = "R1001"
    INVALID_REPORT_DATA = "R1002"
    REPORT_TEMPLATE_NOT_FOUND = "R1003"
    REPORT_FORMAT_ERROR = "R1004"

    # 数据处理错误 (2000-2999)
    DATA_INSUFFICIENT = "D2001"
    DATA_FORMAT_INVALID = "D2002"
    DATA_PROCESSING_FAILED = "D2003"
    DATA_SOURCE_ERROR = "D2004"

    # 图表生成错误 (3000-3999)
    CHART_GENERATION_FAILED = "C3001"
    INVALID_CHART_DATA = "C3002"
    CHART_FORMAT_ERROR = "C3003"

    # 导出错误 (4000-4999)
    EXPORT_FAILED = "E4001"
    EXPORT_FORMAT_UNSUPPORTED = "E4002"
    FILE_ACCESS_ERROR = "E4003"
    DISK_SPACE_INSUFFICIENT = "E4004"

    # 配置错误 (5000-5999)
    CONFIG_INVALID = "C5001"
    CONFIG_NOT_FOUND = "C5002"
    CONFIG_LOAD_FAILED = "C5003"

    # 系统错误 (6000-6999)
    SYSTEM_ERROR = "S6001"
    NETWORK_ERROR = "S6002"
    TIMEOUT_ERROR = "S6003"
    MEMORY_INSUFFICIENT = "S6004"


# 错误处理装饰器
def handle_report_errors(default_return=None):
    """报告错误处理装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ReportError:
                # 重新抛出已知的报告错误
                raise
            except Exception as e:
                # 将未知异常包装为ReportGenerationError
                raise ReportGenerationError(
                    f"未知错误: {str(e)}",
                    error_code=ErrorCodes.SYSTEM_ERROR,
                    original_error=e
                )
        return wrapper
    return decorator


def validate_report_data(data: dict) -> list:
    """验证报告数据"""
    errors = []

    # 验证必需字段
    required_fields = ['report_type', 'created_at']
    for field in required_fields:
        if field not in data:
            errors.append(f"缺少必需字段: {field}")

    # 验证报告类型
    if 'report_type' in data and not isinstance(data['report_type'], str):
        errors.append("报告类型必须是字符串")

    # 验证创建时间
    if 'created_at' in data and not hasattr(data['created_at'], 'strftime'):
        errors.append("创建时间必须是datetime对象")

    return errors


def create_error_response(error: Exception) -> dict:
    """创建错误响应"""
    response = {
        'success': False,
        'error': str(error),
        'error_type': error.__class__.__name__
    }

    # 添加特定错误类型的额外信息
    if isinstance(error, ReportGenerationError):
        response['error_code'] = error.error_code
    elif isinstance(error, ReportValidationError):
        response['field_name'] = error.field_name
        response['validation_errors'] = error.validation_errors
    elif isinstance(error, ReportExportError):
        response['export_format'] = error.export_format
        response['file_path'] = error.file_path
    elif isinstance(error, ChartGenerationError):
        response['chart_type'] = error.chart_type
        response['chart_id'] = error.chart_id

    return response