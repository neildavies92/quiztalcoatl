# Container runtime

Docker is an additional local/CI execution environment. Native uv development remains supported.
There is one CLI image, no server, ports, services, database, registry publication or startup download.
Country facts, recipes and assets are mounted at run time: changing editorial data needs no rebuild.
The real V-001 snapshot is still draft and `resolve` continues to reject it.

## Build and check

Requires a running Docker Engine (Docker Desktop on macOS, or Docker Engine/Desktop with WSL2 on
Windows), Make and host `python3` 3.9+ for the standard-library acceptance driver. The application
and its dependencies execute inside the image with Python 3.12.16; no host Pillow/FFmpeg is needed
for the Docker targets. Use a non-root host developer/CI account for ownership acceptance.

```bash
make docker-build
make docker-check
make docker-smoke
```

- `docker-build` builds `quiztalcoatl:local`, the default runtime target.
- `docker-check` builds `quiztalcoatl:test`, then executes the existing `make check` and `make smoke`
  inside real containers with `--network none`. Locked dev dependencies exist only in this stage.
- `docker-smoke` exercises the actual runtime image offline: help/version/doctor, non-root execution,
  no dev tools, Pillow/fonts, read-only mounts, host-user output ownership/read/delete, unchanged
  input hashes, draft rejection, approved **synthetic** resolution and real libx264/ffprobe encoding.
  It keeps only `output/container-smoke/smoke.mp4` for host playback UAT. Synthetic input/review
  metadata and manifest files are temporary test-only material and are removed automatically.

Override tags/output location with `DOCKER_IMAGE`, `DOCKER_TEST_IMAGE` and `DOCKER_SMOKE_DIR` Make
variables. Build the runtime before `docker-smoke`. Docker build needs network access to image,
Debian and Python package repositories; normal application execution needs none.

## Image stages and pins

`base` installs FFmpeg/ffprobe, Fontconfig and DejaVu, removes package-manager caches and Python pip,
and creates UID/GID 10001. `build` installs the application non-editably with
`uv sync --locked --no-dev --no-editable`; only its production virtual environment reaches
`runtime`. `test` has an editable checkout, Make and locked dev tools to preserve the existing
uv-based development commands. Its writable project directory belongs to the non-root test user.
The final runtime contains neither test/developer tools nor the repository's data/recipes/assets,
Git metadata, local `.env` files, caches or generated video outputs.

The Dockerfile pins these multi-architecture image indexes, verified against their registries:

| Image | Index digest |
| --- | --- |
| `python:3.12.16-slim-bookworm` | `sha256:6dd8b6dab6b3adc7812bab69eca5dbdc1a5cc690ad28306d234ffb4ef8ac9753` |
| `ghcr.io/astral-sh/uv:0.11.19` | `sha256:b46b03ddfcfbf8f547af7e9eaefdf8a39c8cebcba7c98858d3162bd28cf536f6` |

An index selects the appropriate Linux architecture, including local arm64 and CI amd64. uv uses
the base interpreter with `UV_PYTHON_DOWNLOADS=never`, so `.python-version` cannot trigger a second,
unpinned Python download. Runtime installs use the unchanged committed `uv.lock`, including its
platform-specific wheel hashes. The Python image is the [official image](https://hub.docker.com/_/python);
the uv stage follows [Astral's documented Docker integration](https://docs.astral.sh/uv/guides/integration/docker/).

These are **not bit-for-bit image rebuild guarantees**: Debian repositories/packages are not
snapshot-pinned, and the existing build backend has a bounded version range outside the application's
runtime lock. Debian package/security updates and a different architecture may change system/native
libraries and encoded media bytes. Content/resolver logic and its existing deterministic ranking
are unchanged. Image/font/native-library pin changes should be reviewed before accepting new pixel
or media baselines. Build-time arguments can override image references explicitly; the defaults
above remain immutable pins. This milestone does not add another dependency-lock framework.

The runtime is about 551 MiB uncompressed on the tested arm64 build, primarily standard Debian
FFmpeg libraries. Its build/test tools and their dependencies are excluded from the final image.
`.dockerignore` allows only public project inputs needed by the build/test stages, then excludes
common secret/environment files, virtual environments, Git internals, caches, output and videos
again within those trees. Runtime uses selective copies; no blanket repository copy enters it.

## Fonts and graphics interface

The runtime installs Debian's [`fonts-dejavu-core`](https://packages.debian.org/bookworm/fonts-dejavu-core)
and `fontconfig`. The agreed graphics contract is:

```text
QUIZTALCOATL_FONT_DIR=/usr/share/fonts/truetype/dejavu
DejaVuSans.ttf
DejaVuSans-Bold.ttf
```

Graphics may accept an explicit font directory or resolve this environment variable. It must not
silently depend on a workstation's implicit font. No font binaries are newly committed to this
repository. Debian retains the fonts' copyright/licence notices at
`/usr/share/doc/fonts-dejavu-core/copyright` and author list beside it. The package identifies the
Bitstream Vera licence for the base fonts, with DejaVu changes in the public domain; notices remain
in the distributed image. This is separate from editorial flag-artwork rights.

Inspect available fonts/licences without networking:

```bash
docker run --rm --network none --entrypoint fc-match quiztalcoatl:local 'DejaVu Sans'
docker run --rm --network none --entrypoint cat quiztalcoatl:local \
  /usr/share/doc/fonts-dejavu-core/copyright
```

A provisional cross-branch integration was executed using read-only graphics source/helper
overlays in the actual runtime, with networking disabled and a read-only root filesystem. Six
host-accessible synthetic PNGs (1920×1080 and 480×270) were generated under the graphics worktree’s
`output/container-design-integration/`; two container runs produced identical bytes. Native macOS
and Linux raster pixels differed, so pixel determinism is qualified to the controlled container
font/library environment. This preparation check is not human design approval.

After the graphics branch merges, rebuild and run its documented synthetic preview helper from the
actual installed package inside this runtime, using the same font directory and writable output mount. Recheck full-HD PNG dimensions, measured
text geometry, preserved flag proportions and host read/delete access. M3c supplies the environment;
it does not implement graphics, visual-theme approval or a video timeline.

## CLI and input/output mounts

The entry point is the installed `quiztalcoatl` command; normal arguments follow the image name:

```bash
docker run --rm quiztalcoatl:local --help
docker run --rm quiztalcoatl:local --version
docker run --rm --network none quiztalcoatl:local doctor
```

From the repository root on Linux, macOS or WSL, create the output directory as the host user and
map its numeric UID/GID. This avoids root-owned output on Linux and is exercised on macOS Docker
Desktop by the acceptance driver. No writable source checkout or Docker socket is mounted inside
an application container. The default image user is already non-root (10001:10001); `--user` maps
another non-root developer's identity for bind-mounted output. SELinux or remote-daemon setups may
require local mount-policy configuration; they are not claimed tested by Linux CI/macOS UAT.

```bash
mkdir -p output

docker run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  --user "$(id -u):$(id -g)" \
  --mount "type=bind,src=$PWD/data,dst=/work/data,readonly" \
  --mount "type=bind,src=$PWD/recipes,dst=/work/recipes,readonly" \
  --mount "type=bind,src=$PWD/assets,dst=/work/assets,readonly" \
  --mount "type=bind,src=$PWD/output,dst=/work/output" \
  quiztalcoatl:local resolve \
  --countries /work/data/countries.json --recipe /work/recipes/V-001.json \
  --content-root /work --output /work/output/V-001/manifest.json
```

This currently exits 1 with the real editorial-approval error and creates no manifest. An
`--overwrite` option never bypasses that gate. After actual approved inputs exist, the same command
performs the established atomic manifest publication into the host output mount. The runtime
acceptance driver proves that operation with explicitly synthetic approved inputs, checks byte-
identical repeat manifests/input hashes, and verifies overwrite protection. Production metadata
is never modified to manufacture success.

`/work` is the consistent working/content root. Repository-relative `assets/flags/*.png` paths
therefore remain valid. The acceptance driver also uses a read-only root filesystem, temporary
`/tmp`, dropped capabilities and no-new-privileges. These flags are optional runtime hardening,
not an alternative application mode or dependency on a background service.

## Manual developer UAT

Actual automated execution was performed on macOS Docker Desktop / Linux arm64. CI exercises Linux
amd64 separately. A Linux pass does not certify Windows/WSL or every host mount policy.

- [ ] Run the three Docker Make targets above; all return 0.
- [ ] Run help/version/doctor directly; package/Python/media-tool versions appear and doctor returns 0.
- [ ] Open `output/container-smoke/smoke.mp4` on the host (`open` on macOS, `xdg-open` on a Linux
  desktop, or the host file manager/player from WSL). Confirm visible moving synthetic video,
  approximately two seconds, and normal playback. **Human playback assessment is pending.**
- [ ] Read/copy/delete the host MP4 as the ordinary developer, without sudo; then rerun
  `make docker-smoke` to recreate it. Automated acceptance already checks host read/delete and
  numeric ownership on an adjacent test file and reads/verifies the MP4.
- [ ] Confirm data/recipes/assets remain unchanged (`git status --short` and the acceptance driver's
  before/after input SHA-256 comparison). The deliberate write test returns read-only-filesystem.
- [ ] Confirm offline operations succeed with `--network none`, including real synthetic resolution
  and FFmpeg work; no startup package/font downloads occur.
- [ ] Run the real draft resolution command above; confirm useful approval diagnostics and absent
  output. Its failure is expected until human editorial acceptance, regardless of image/CI status.
- [ ] When both branches are integrated, run the synthetic graphics previews in this image and
  inspect both full-HD and mobile-scale output. Human design UAT remains a separate acceptance.

No Docker Compose, deployment, registry publication, GPU, scheduling, rendering application logic,
editorial approval or publishing automation is introduced.
