#!/usr/bin/env python3

# root build script: writes build.ninja for the web build (`ninja web`)

import argparse
import io
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from tools import ninja_syntax
from tools.web_build import generate_web_build, web_configure_inputs

parser = argparse.ArgumentParser()
parser.add_argument(
    "--compiler-launcher",
    metavar="BINARY",
    help="a program that runs each compile, such as ccache",
)
parser.add_argument(
    "--release",
    action="store_true",
    help="release build: assertions are not checked (the debug build stops at the first failed assertion)",
)
parser.add_argument(
    "--web-emcc",
    type=str,
    help="Emscripten's emcc for `ninja web` (default: emcc on the PATH, then EMSDK's or ~/emsdk's)",
)
args = parser.parse_args()

# the settings the build reads
sln = SimpleNamespace(
    build_dir=Path("build"),
    compiler_launcher=args.compiler_launcher,
    port_release=args.release,
    web_emcc=args.web_emcc,
)

# build.ninja
out = io.StringIO()
n = ninja_syntax.Writer(out)
n.variable("ninja_required_version", "1.3")
n.newline()

configure_script = Path(os.path.relpath(os.path.abspath(sys.argv[0])))
n.comment("The arguments passed to configure.py, for rerunning it.")
n.variable(
    "configure_args",
    [f'"{arg}"' if any(ch.isspace() for ch in arg) else arg for arg in sys.argv[1:]],
)
n.variable("python", f'"{sys.executable}"')
n.newline()

generate_web_build(n, sln)

n.comment("Reconfigure on change")
n.rule(
    name="configure",
    command=f"$python {configure_script} $configure_args",
    generator=True,
    description=f"RUN {configure_script}",
)
n.build(
    outputs="build.ninja",
    rule="configure",
    implicit=[configure_script, Path("tools/ninja_syntax.py"), *web_configure_inputs()],
)
n.newline()

if "\nbuild web: " not in out.getvalue():
    sys.exit("configure.py: the web build was not generated: emcc was not found "
             "(put it on the PATH, e.g. `source ~/emsdk/emsdk_env.sh`, or pass --web-emcc)")
n.comment("Default rule: the web build")
n.default("web")

with open("build.ninja", "w", encoding="utf-8") as f:
    f.write(out.getvalue())
out.close()
