"""satsumas — an SDR weather-satellite ground station with cloud segmentation.

Convention, established at S0 and not broken afterwards: ``satsumas.<module>``
is importable from anywhere, including notebooks. Notebooks import; they do not
define.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("satsumas")
except PackageNotFoundError:  # pragma: no cover - source tree without install
    __version__ = "0.0.0"

__all__ = ["__version__"]
