import os
import platform as _plat

try:
    from ._version import __version__
except ImportError:
    __version__ = "unknown"

from .core import (
    BinaryNotFoundError,
    BuildInfoError,
    LlamaCppBinError,
    get_binary_path,
    get_build_info,
    run_server,
)


def _fix_symlinks():
    if _plat.system() == "Windows":
        return

    import json

    bin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
    manifest = os.path.join(bin_dir, "_symlinks.json")
    if not os.path.exists(manifest):
        return

    with open(manifest, encoding="utf-8") as f:
        symlinks = json.load(f)

    for name, target in symlinks.items():
        link = os.path.join(bin_dir, name)
        if os.path.lexists(link):
            try:
                os.remove(link)
            except OSError:
                pass
        try:
            os.symlink(target, link)
        except OSError:
            pass

    try:
        os.remove(manifest)
    except OSError:
        pass


_fix_symlinks()
