class OperagentsException(Exception):
    """Base class for all exceptions raised by operagents"""


class OperaFinished(OperagentsException):
    """Raised when no more scenes are available and the opera has finished"""


class SceneFinished(OperagentsException):
    """Raised when the scene has already finished.

    No more characters can act after the scene has finished.
    """


class BackendError(OperagentsException):
    """Raised when the backend fails to process the request"""
