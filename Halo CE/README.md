# Games site: OpenCE (Halo: Combat Evolved) web port

A GitHub Pages site with a launcher page where you pick the game to play.
The game here is the web (WebAssembly) port of
[OpenCE](https://github.com/OpenCommunityEdition/OpenCE), the Halo: Combat
Evolved decompilation. This repository holds only what that web build and
the site need.

The site serves no game data: the player gives the page their own Xbox disc
image, and the page copies the maps into the browser's storage. Nothing is
uploaded.

## Layout

| Path | What it is |
| --- | --- |
| `site/` | Published as the site's root: the launcher `index.html`, and any other games you keep in folders there |
| `port/web/site/` | The game's page, service worker and importers; built into `/halo/` |
| `port/web/src/`, `port/linux/`, `source/`, `port/third_party/`, `port/assets/` | The game, its platform layer and what the web build compiles |
| `configure.py`, `tools/` | The build (Ninja graph, site assembly, a local server) |
| `.github/workflows/pages.yml` | Builds with Emscripten and deploys to GitHub Pages |

## Deploying

1. Push to `main`.
2. Settings > Pages > Build and deployment > Source: **GitHub Actions**.

The workflow builds the game and publishes `site/` at the root with the game
at `/halo/`.

## Adding another game

Put its static files in `site/<name>/` (with an `index.html`), and copy the
commented card in `site/index.html`. Keep the folder name different from
`halo`.

## Building locally

Install Emscripten 6.0.10 ([emsdk](https://emscripten.org/docs/getting_started/downloads.html))
and Ninja, then:

```sh
source ~/emsdk/emsdk_env.sh
python configure.py --release      # --web-emcc PATH if emcc is not on the PATH
ninja web                          # build/web/site/
python tools/assemble_site.py      # dist/: launcher + game at /halo/
python tools/web_serve.py          # http://localhost:8000/
```

The first build fetches SDL 3.4.16's source as an Emscripten port.
Details of the web port: [port/web/README.md](port/web/README.md).

## Licence

The game and the port are under the GNU AGPL-3.0 (`LICENSE`); the
third-party libraries' licences are in `LICENSES/` and beside their sources
in `port/third_party/`. Halo is a trademark of Microsoft; this is not
affiliated with Microsoft or Bungie.
