"""Build helpers for the web build (tools/web_build.py): where the game's sources,
the XDK declarations and the third-party libraries are, and how their units
are compiled. They were the native Linux build's; the web build is the only
build this repository keeps, so they live here."""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

PORT_DIR = Path("port/linux")

PORT_CONFIG = PORT_DIR / "port.json"

# the Xbox SDK declarations the game and the platform layer use, in place of
# the SDK's headers (port/include/xdk/README.md)
XDK_INCLUDE = Path("port/include/xdk")

def xdk_headers() -> List[Path]:
    return sorted(XDK_INCLUDE.glob("*.h"))

def game_sources(config: Dict[str, Any]) -> List[Path]:
    """the game's C sources (port.json "game"): every one under its root but
    those excluded (a file, or a folder: a name ending in "/")"""
    game = config["game"]
    excluded = game.get("exclude", [])
    return sorted(
        source for source in Path(game["root"]).rglob("*.c")
        if not any(source.as_posix() == name or (name.endswith("/") and source.as_posix().startswith(name))
                   for name in excluded)
    )

def game_defines_and_includes(config: Dict[str, Any]) -> str:
    """the game sources' defines and include directories (port.json "game")"""
    game = config["game"]
    return " ".join(
        [f"-D{define}" for define in game.get("defines", [])]
        + [f"-I{_quote(Path(directory))}" for directory in game.get("include_dirs", [])]
    )

def compile_launcher(sln: Any) -> str:
    """what the native ports' compile commands start with: the
    --compiler-launcher (ccache, say) and a space, or nothing"""
    launcher = getattr(sln, "compiler_launcher", None)
    return f"{launcher} " if launcher else ""

# the TOML parser the platform layer reads config.toml with (port_config.c)
TOML_DIR = Path("port/third_party/tomlc17")

EXPAT_DIR = Path("port/third_party/expat")

EXPAT_SOURCES = ("xmlparse.c", "xmlrole.c", "xmltok.c")

KCP_DIR = Path("port/third_party/kcp")

MONOCYPHER_DIR = Path("port/third_party/monocypher")

MUSL_MATH_DIR = Path("port/third_party/musl-math")

# the port's zlib (port/third_party/zlib/zlib_prefixed.h): what inflates the
# maps, the menus' and the HUD's PNGs and the updates, data from anywhere,
# instead of the game's own 1.1.3 (its inflate only, its names prefixed z_)
ZLIB_DIR = Path("port/third_party/zlib")

ZLIB_SOURCES = ("adler32.c", "crc32.c", "inffast.c", "inflate.c", "inftrees.c", "uncompr.c", "zutil.c")

# (its names prefixed, and the one Z_PREFIX leaves, its error messages, which
# the game's zlib names the same)
ZLIB_DEFINES = ("-DZ_PREFIX", "-Dz_errmsg=z_port_errmsg")

# the Custom Edition maps' Ogg Vorbis decoder (custom_edition_sounds.c),
# compiled as the port's game units are
STB_VORBIS_SOURCE = Path("port/third_party/stb_vorbis/stb_vorbis.c")

def build_repository() -> str:
    """the GitHub repository a build is made from, owner/name, which a client
    tells the servers it joins (network_distributed.c): CI's
    GITHUB_REPOSITORY, else the checkout's origin remote's (its credentials
    left out: only the owner and the name are kept), else none"""
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if not repository:
        try:
            url = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True,
                                 timeout=10, check=False).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            url = ""
        found = re.search(r"github\.com[:/]+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/*$", url)
        repository = found.group(1) if found else ""
    return repository if re.fullmatch(r"[A-Za-z0-9_.-]{1,39}/[A-Za-z0-9_.-]{1,100}", repository) else ""

def updater_defines(release: bool) -> str:
    """the self-updater's build (port/linux/src/updater.c): its number, from
    HALO_BUILD_NUMBER (tools/ci_build.py gives it for builds of main; none
    elsewhere, which never look for updates), its configuration, and the
    repository it is made from (build_repository)"""
    number = os.environ.get("HALO_BUILD_NUMBER", "0")
    if not number.isdigit():
        number = "0"
    flavor = "release" if release else "debug"
    return (f'-DHALO_BUILD_NUMBER={number} -DHALO_BUILD_FLAVOR=\\"{flavor}\\" '
            f'-DHALO_BUILD_REPOSITORY=\\"{build_repository()}\\"')

def configuration_defines(sln: Any) -> List[str]:
    """what configure.py's options define for every unit of a native build:
    --release (no assertions), --profile (the profiling build's recording,
    port/linux/src/profile_trace.c)"""
    defines = []
    if getattr(sln, "port_release", False):
        defines.append("-DHALO_RELEASE")
    if getattr(sln, "port_profile", False):
        defines.append("-DHALO_PROFILE")
    return defines

# voice chat's codec (port/third_party/opus; network_voice.c): the
# floating-point library in plain C, its files as sources.txt lists them
OPUS_DIR = Path("port/third_party/opus")

OPUS_DEFINES = ("-DOPUS_BUILD", "-DVAR_ARRAYS", "-DHAVE_LRINTF", "-DHAVE_LRINT")

def opus_sources() -> List[Path]:
    """Opus's library sources (port/third_party/opus/sources.txt)"""
    return [OPUS_DIR / line.strip() for line in (OPUS_DIR / "sources.txt").read_text().splitlines() if line.strip()]

def opus_cflags(abi: str) -> str:
    """the flags Opus's sources build with, on the platform layer's ABI"""
    return " ".join([abi, "-std=gnu11", "-O2", *OPUS_DEFINES, *(f"-I{OPUS_DIR / name}" for name in
                                                            ("include", "celt", "silk", "silk/float")), "-w"])

def musl_math_sources() -> List[Path]:
    """musl's maths functions the game uses (port/third_party/musl-math)"""
    return sorted((MUSL_MATH_DIR / "src").glob("*.c"))

def musl_math_cflags(abi: str) -> str:
    """their flags: the game's ABI, and the headers standing in for musl's"""
    return " ".join([abi, "-std=gnu11", "-w", f"-I{MUSL_MATH_DIR}/include",
                     f"-include {MUSL_MATH_DIR}/include/libm.h"])


def _quote(path: Any) -> str:
    text = str(path).replace(os.sep, "/")
    return f'"{text}"' if " " in text else text


# game files that call variadic functions without a prototype in scope, which
# only works where the callee's type is spelled out: they get a prototype
# header (port/android/include/halo_android_variadic_prototypes.h)
VARIADIC_PROTOTYPE_FILES = {
    "source/ai/action_uncover.c", "source/ai/ai.c", "source/ai/ai_debug.c",
    "source/bungie_net/common/public_key_crypt.c", "source/camera/editor_flying_camera.c",
    "source/game/cheats.c", "source/game/game_engine.c", "source/game/players.c",
    "source/hs/hs.c", "source/interface/hud_nav_points.c",
    "source/networking/telnet_console.c", "source/rasterizer/xbox/rasterizer_xbox_errors.c",
    "source/render/render.c",
}


def game_configure_inputs() -> List[Path]:
    """Files whose change must re-run configure.py: the port's settings, its
    sources' folders (so that adding or removing a source re-runs it)."""
    if not PORT_CONFIG.is_file():
        return [Path(__file__)]
    with open(PORT_CONFIG, "r", encoding="utf-8") as f:
        config = json.load(f)
    game_folders = sorted({source.parent for source in game_sources(config)})
    return [PORT_CONFIG, Path(__file__), PORT_DIR / "src", PORT_DIR / "game", XDK_INCLUDE, *game_folders]
