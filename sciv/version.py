from importlib.metadata import PackageNotFoundError, version

try:
    import pkg_resources
except ImportError:
    pkg_resources = None  # type: ignore

__major__: int = 0
__minor__: int = 2
__patch__: int = 0
__revision__: int = 1
__isdev__: bool = True

if __isdev__:
    __pre_release__: str = ".dev"
    __build__: str = str(__revision__)
else:
    __pre_release__: str = ""
    __build__: str = ""

__version__: str = f"{__major__}.{__minor__}.{__patch__}{__pre_release__}{__build__}"
__version_name__ = "Proof of Concept - rc1"


def get_package_version(package_name: str) -> str:
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
