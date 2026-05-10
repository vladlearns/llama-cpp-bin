# llama-cpp-bin

Pre-built llama.cpp server binaries as a py package. Install a wheel for your platform and run it.

## Install

### Pre-built wheels (recommended)

```bash
pip install --index-url https://vladlearns.github.io/llama-cpp-bin/whl/cpu llama-cpp-bin
pip install --index-url https://vladlearns.github.io/llama-cpp-bin/whl/cu124 llama-cpp-bin
pip install --index-url https://vladlearns.github.io/llama-cpp-bin/whl/cu131 llama-cpp-bin
pip install --index-url https://vladlearns.github.io/llama-cpp-bin/whl/rocm llama-cpp-bin
pip install --index-url https://vladlearns.github.io/llama-cpp-bin/whl/vulkan llama-cpp-bin
```

### PyPI (builds from source)

If no pre-built wheel matches your platform, pip falls back to building from the sdist on PyPI:

```bash
pip install llama-cpp-bin
```

You will need CMake, a c++ compiler, and the llama.cpp source submodule.

### Dev

```bash
git clone --recurse-submodules https://github.com/vladlearns/llama-cpp-bin
cd llama-cpp-bin
CMAKE_ARGS="-DGGML_CUDA=ON" pip install -v .
```

## Run

CLI:
```bash
llama-cpp-server -m your-model.gguf --port 8080
```

Python:
```python
from llama_cpp_bin import run_server
proc = run_server("your-model.gguf", port=8080)
proc.wait()
```

Or get the binary path and run it yourself:
```python
import llama_cpp_bin
import subprocess
binary = llama_cpp_bin.get_binary_path()
subprocess.Popen([binary, "--model", "your-model.gguf"])
```
