#!/usr/bin/env python3

import glob
import json
import os
import platform as plat
import shlex
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext as _build_ext

try:
    from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel
except ModuleNotFoundError:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

PACKAGE_NAME = "llama_cpp_bin"
SRC_DIR = Path(__file__).parent / "src"


class CMakeExtension(Extension):
    def __init__(self, name):
        super().__init__(name, sources=[])


class CMakeBuild(_build_ext):
    def run(self):
        for ext in self.extensions:
            self.build_cmake(ext)

    def build_cmake(self, ext):
        cmake_args = shlex.split(os.environ.get("CMAKE_ARGS", ""))
        backend = _get_backend(cmake_args)

        build_dir = Path("build").resolve()
        build_dir.mkdir(parents=True, exist_ok=True)
        llama_cpp_dir = Path(os.environ.get("LLAMA_CPP_DIR", "llama.cpp")).resolve()

        if plat.system() == "Linux":
            cmake_args.extend([
                "-DCMAKE_INSTALL_RPATH=$ORIGIN",
                "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON",
                "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=OFF",
            ])
        elif plat.system() == "Darwin":
            cmake_args.extend([
                "-DCMAKE_INSTALL_RPATH=@loader_path",
                "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON",
                "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=OFF",
            ])

        subprocess.check_call(["cmake", str(llama_cpp_dir)] + cmake_args, cwd=build_dir)

        jobs = os.environ.get("LLAMA_CPP_BUILD_JOBS", "")
        subprocess.check_call(
            ["cmake", "--build", ".", "--config", "Release", "-j" + jobs],
            cwd=build_dir,
        )

        # Copy all files from build/bin to package
        bin_dir = build_dir / "bin"
        if (bin_dir / "Release").is_dir():
            bin_dir = bin_dir / "Release"

        target_dir = Path(self.build_lib) / PACKAGE_NAME / "bin"
        target_dir.mkdir(parents=True, exist_ok=True)

        symlinks = {}
        for f in glob.glob(str(bin_dir / "*")):
            name = os.path.basename(f)
            if os.path.islink(f):
                symlinks[name] = os.readlink(f)
            else:
                shutil.copy(f, target_dir, follow_symlinks=True)

        if symlinks:
            (target_dir / "_symlinks.json").write_text(json.dumps(symlinks))

        # Write build info
        build_info = _build_info(backend, llama_cpp_dir)
        (target_dir.parent / "build_info.json").write_text(json.dumps(build_info, indent=2))

        # Mirror to src/ for editable installs
        src_bin = SRC_DIR / PACKAGE_NAME / "bin"
        src_bin.mkdir(parents=True, exist_ok=True)
        for f in target_dir.iterdir():
            if f.is_file():
                shutil.copy2(f, src_bin / f.name, follow_symlinks=True)
        (SRC_DIR / PACKAGE_NAME / "build_info.json").write_text(json.dumps(build_info, indent=2))


def _get_backend(cmake_args):
    flags = " ".join(cmake_args)
    if "GGML_CUDA" in flags or "LLAMA_CUDA" in flags:
        return "cuda"
    if "GGML_METAL" in flags or "LLAMA_METAL" in flags:
        return "metal"
    if "GGML_HIPBLAS" in flags or "LLAMA_HIPBLAS" in flags or "GGML_HIP" in flags:
        return "rocm"
    if "GGML_VULKAN" in flags or "LLAMA_VULKAN" in flags:
        return "vulkan"
    return "cpu"


def _build_info(backend, llama_cpp_dir):
    commit = "unknown"
    try:
        commit = subprocess.check_output(
            ["git", "-C", str(llama_cpp_dir), "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        pass

    return {
        "llama_cpp_commit": commit,
        "backend": backend,
        "build_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "platform": plat.platform(),
    }


class PlatformBdistWheel(_bdist_wheel):
    def finalize_options(self):
        super().finalize_options()
        self.root_is_pure = False

    def get_tag(self):
        python, abi, plat = super().get_tag()
        return ("py3", "none", plat)


setup(
    ext_modules=[CMakeExtension("llama_cpp_bin_dummy")],
    cmdclass={
        "build_ext": CMakeBuild,
        "bdist_wheel": PlatformBdistWheel,
    },
)
