from importlib.metadata import PackageNotFoundError, version

# Try importing pkg_resources, if available.
try:
    import pkg_resources
except ImportError:
    pkg_resources = None

__major__: int = 0
__minor__: int = 1
__patch__: int = 2

__version__: str = f"{__major__}.{__minor__}.{__patch__}"
__version_name__ = "Alpha"


def get_package_version(package_name: str) -> str:
    """Retrieve the version of a package using importlib.metadata with a fallback to pkg_resources."""
    try:
        return version(package_name)
    except PackageNotFoundError:
        if pkg_resources:
            try:
                return pkg_resources.get_distribution(package_name).version
            except pkg_resources.DistributionNotFound:
                return "unknown"
        return "unknown"


__panda3d_version__ = get_package_version("panda3d")
__kivy_version__ = get_package_version("kivy")
