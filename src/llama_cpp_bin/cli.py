import argparse
import os
import sys

from .core import BinaryNotFoundError, BuildInfoError, get_binary_path, get_build_info, run_server


def _env(name):
    val = os.environ.get(name, "").strip()
    return val or None


def _env_int(name, parser):
    raw = _env(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        parser.error(f"{name}={raw} is not a valid integer")


def _parser():
    p = argparse.ArgumentParser(prog="llama-cpp-server", description="Run llama.cpp HTTP server.")
    p.add_argument("-m", "--model", help="Path to GGUF model file")
    p.add_argument("--host", help="Host to bind (default: 127.0.0.1)")
    p.add_argument("--port", type=int, help="Port to listen on (default: 8080)")
    p.add_argument("--ctx-size", dest="ctx_size", type=int, help="Context size in tokens")
    p.add_argument("--n-gpu-layers", dest="n_gpu_layers", type=int, help="GPU layers to offload")
    p.add_argument("--info", action="store_true", help="Print build info and exit")
    p.add_argument(
        "passthrough",
        nargs=argparse.REMAINDER,
        help=argparse.SUPPRESS,
    )
    return p


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)

    if args.info:
        try:
            info = get_build_info()
            print("Build info:")
            for key, val in info.items():
                if val is not None:
                    print(f"  {key}: {val}")
        except BuildInfoError as exc:
            print(f"Warning: {exc}", file=sys.stderr)
        try:
            binary = get_binary_path()
            print(f"  binary_path: {binary}")
        except BinaryNotFoundError:
            print("  binary_path: NOT FOUND", file=sys.stderr)
        return 0

    model = args.model or _env("LLAMA_MODEL_PATH")
    if not model:
        parser.error("No model path provided")

    host = args.host or _env("LLAMA_HOST") or "127.0.0.1"
    if args.port is not None:
        port = args.port
    else:
        port = _env_int("LLAMA_PORT", parser) or 8080

    ctx_size = args.ctx_size or _env_int("LLAMA_CTX_SIZE", parser)
    n_gpu_layers = args.n_gpu_layers or _env_int("LLAMA_N_GPU_LAYERS", parser)

    passthrough = args.passthrough or []
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]

    extra = list(passthrough)
    if ctx_size is not None:
        extra.extend(["--ctx-size", str(ctx_size)])
    if n_gpu_layers is not None:
        extra.extend(["--n-gpu-layers", str(n_gpu_layers)])

    try:
        binary = get_binary_path()
    except BinaryNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Starting: {binary} --model {model} --host {host} --port {port}")
    try:
        proc = run_server(model=model, host=host, port=port, extra_args=extra or None)
        proc.wait()
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 0
    except OSError as exc:
        print(f"Error: Failed to launch server: {exc}", file=sys.stderr)
        return 1

    return proc.returncode if proc.returncode is not None else 0


if __name__ == "__main__":
    sys.exit(main())
