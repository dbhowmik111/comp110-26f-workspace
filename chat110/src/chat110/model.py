"""Download one verified Gemma bundle from R2; never contact Hugging Face."""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tarfile
import tempfile
from http.client import HTTPException
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
BUNDLE_CONFIG = ROOT / "model_bundle.json"
MODEL_FILES = (
    "added_tokens.json",
    "chat_template.jinja",
    "config.json",
    "generation_config.json",
    "model.safetensors",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer.model",
    "tokenizer_config.json",
)
DOCUMENT_FILES = (
    "NOTICE",
    "MODEL_USE.md",
    "MODEL_CARD.md",
    "licenses/GEMMA_TERMS_OF_USE.md",
    "licenses/GEMMA_PROHIBITED_USE_POLICY.md",
)
BUNDLE_FILES = (*MODEL_FILES, *DOCUMENT_FILES, "PROVENANCE.json")
CHUNK_SIZE = 1024 * 1024


class BundleError(Exception):
    """A model bundle could not be downloaded or installed."""


def load_config() -> dict:
    try:
        return json.loads(BUNDLE_CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise BundleError(f"Could not read {BUNDLE_CONFIG.name}: {error}") from error


def file_sha256(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def _is_installed(path: Path, config: dict) -> bool:
    marker = path / ".bundle-sha256"
    return (
        marker.is_file()
        and marker.read_text(encoding="ascii").strip() == config["sha256"]
        and all(
            (path / name).is_file()
            and (path / name).stat().st_size == info["size_bytes"]
            for name, info in config["files"].items()
        )
    )


def _download(url: str, destination: Path, config: dict) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise BundleError("The model bundle URL must use HTTPS.")
    request = Request(url, headers={"User-Agent": "chat110/0.1"})
    digest = hashlib.sha256()
    downloaded = 0
    reported = -1
    print(
        "Download progress updates in increments of 10%.\n"
        "If progress appears stuck for more than 1 minute, press Ctrl+C to cancel, "
        "then run the command again to retry.",
        file=sys.stderr,
        flush=True,
    )
    try:
        with urlopen(request, timeout=60) as response, destination.open("wb") as output:
            if urlparse(response.geturl()).scheme != "https":
                raise BundleError("The bundle download redirected away from HTTPS.")
            while chunk := response.read(CHUNK_SIZE):
                downloaded += len(chunk)
                if downloaded > config["size_bytes"]:
                    raise BundleError("Download exceeds the expected bundle size.")
                output.write(chunk)
                digest.update(chunk)
                percent = downloaded * 100 // config["size_bytes"]
                if percent // 10 != reported:
                    print(f"Downloading Gemma: {percent}%", file=sys.stderr)
                    reported = percent // 10
    except (URLError, TimeoutError, HTTPException) as error:
        # Do not echo the URL: a private R2 URL may contain a signed query string.
        raise BundleError(
            "Could not download the bundle. Check the R2 URL, access, and network, "
            "then retry."
        ) from error
    if downloaded != config["size_bytes"] or digest.hexdigest() != config["sha256"]:
        raise BundleError("Bundle size or SHA-256 mismatch; nothing was installed.")


def _unpack(archive_path: Path, destination: Path, config: dict) -> None:
    """Copy only known regular files, without following archive paths or links."""
    seen = set()
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive:
            if member.name not in BUNDLE_FILES or member.name in seen or not member.isfile():
                raise BundleError(f"Unexpected or unsafe archive member: {member.name!r}")
            info = config["files"][member.name]
            if member.size != info["size_bytes"]:
                raise BundleError(f"Unexpected size for {member.name}.")
            target = destination / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise BundleError(f"Missing archive data for {member.name}.")
            with source, target.open("xb") as output:
                shutil.copyfileobj(source, output, CHUNK_SIZE)
            if file_sha256(target) != info["sha256"]:
                raise BundleError(f"SHA-256 mismatch for {member.name}.")
            seen.add(member.name)
    if seen != set(BUNDLE_FILES):
        raise BundleError("The bundle is missing required model or attribution files.")


def ensure_model(
    *, url: str | None = None, archive: Path | None = None, cache_dir: Path | None = None,
) -> Path:
    """Install atomically on first use, then reuse the local model without network I/O."""
    config = load_config()
    checksum = config.get("sha256", "")
    if (
        len(checksum) != 64
        or any(char not in "0123456789abcdef" for char in checksum)
        or config.get("size_bytes", 0) <= 0
        or set(config.get("files", {})) != set(BUNDLE_FILES)
    ):
        raise BundleError("Build the bundle first: uv run python build_model_bundle.py")
    cache_dir = cache_dir if cache_dir is not None else ROOT / ".cache" / "gemma3-r2"
    model_dir = cache_dir / checksum
    if _is_installed(model_dir, config):
        return model_dir
    if model_dir.exists():
        raise BundleError(f"Incomplete model cache. Remove {model_dir} and retry.")
    url = url or os.environ.get("GEMMA_MODEL_URL") or config.get("url")
    if archive is None and not url:
        raise BundleError(
            f"Set the R2 HTTPS download URL in {BUNDLE_CONFIG.name} (the url field) "
            "or in GEMMA_MODEL_URL. See README.md for upload instructions."
        )
    print(
        "Gemma 3 270M IT by Google DeepMind. Use is subject to MODEL_USE.md and "
        "the Gemma Terms of Use: https://ai.google.dev/gemma/terms",
        file=sys.stderr,
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix=".install-", dir=cache_dir) as temporary:
            staging = Path(temporary)
            if archive is None:
                archive = staging / "bundle.tar.gz"
                _download(url, archive, config)
            elif archive.stat().st_size != config["size_bytes"] or file_sha256(archive) != checksum:
                raise BundleError("Bundle size or SHA-256 mismatch; nothing was installed.")
            extracted = staging / "model"
            extracted.mkdir()
            print("Verifying and unpacking Gemma…", file=sys.stderr)
            _unpack(archive, extracted, config)
            (extracted / ".bundle-sha256").write_text(checksum + "\n", encoding="ascii")
            try:
                extracted.rename(model_dir)
            except OSError:
                # Another process may have completed the same installation first.
                if not _is_installed(model_dir, config):
                    raise
    except (OSError, tarfile.TarError, EOFError) as error:
        raise BundleError(f"Could not install the model bundle: {error}") from error
    return model_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--url", help="R2 HTTPS URL; overrides the configured URL")
    source.add_argument("--archive", type=Path, help="Install an already-downloaded bundle")
    args = parser.parse_args()
    try:
        print(ensure_model(url=args.url, archive=args.archive))
    except BundleError as error:
        parser.exit(1, f"Model setup failed: {error}\n")


if __name__ == "__main__":
    main()
