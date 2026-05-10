import json
import os
import subprocess
import sys
from pathlib import Path
from importlib.resources import files as _pkg_files


class LlamaCppBinError(RuntimeError):
    pass


class BinaryNotFoundError(LlamaCppBinError):
    pass


class BuildInfoError(LlamaCppBinError):
    pass


def _bin_name():
    return "llama-server.exe" if os.name == "nt" else "llama-server"


def _pkg_path(relative):
    return Path(str(_pkg_files("llama_cpp_bin").joinpath(relative)))


def get_binary_path():
    candidate = _pkg_path(f"bin/{_bin_name()}")
    if not candidate.is_file():
        raise BinaryNotFoundError("Binary not found. Run: CMAKE_ARGS='-DGGML_CUDA=ON' pip install -v .")
    return candidate


def get_build_info():
    info_path = _pkg_path("build_info.json")
    if not info_path.is_file():
        raise BuildInfoError("build_info.json not found")
    raw = info_path.read_text(encoding="utf-8")
    return json.loads(raw)


def run_server(model, host="127.0.0.1", port=8080, extra_args=None, env=None):
    binary = get_binary_path()

    if not model or not model.strip():
        raise ValueError("model path required")

    if not Path(model).is_file():
        raise FileNotFoundError(f"Model not found: {model}")

    if not (1 <= port <= 65535):
        raise ValueError(f"invalid port: {port}")

    cmd = [str(binary), "--model", str(model), "--host", str(host), "--port", str(port)]
    if extra_args:
        cmd.extend(extra_args)

    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)

    return subprocess.Popen(cmd, env=proc_env, stdout=sys.stdout, stderr=sys.stderr)
