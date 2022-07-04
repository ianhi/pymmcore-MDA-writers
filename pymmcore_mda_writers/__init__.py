try:
    from ._version import version as __version__
except ImportError:  # pragma: no cover
    __version__ = "unknown"  # pragma: no cover
__author__ = "Ian Hunt-Isaak"
__email__ = "ianhuntisaak@gmail.com"

from ._writers import BaseWriter, SimpleMultiFileTiffWriter, ZarrWriter

__all__ = [
    "__version__",
    "BaseWriter",
    "SimpleMultiFileTiffWriter",
    "ZarrWriter",
]
