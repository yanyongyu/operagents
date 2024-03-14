class OperaFinished(Exception):
    """Raised when no more scenes are available and the opera has finished"""


class SceneFinished(Exception):
    """Raised when the scene has already finished.

    No more characters can act after the scene has finished.
    """
