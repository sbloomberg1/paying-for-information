"""Create a release spec from the actual pushed image digests."""
import argparse
import json
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument("--repository", required=True)
parser.add_argument("--tag", required=True)
parser.add_argument("--player", required=True)
parser.add_argument("--referee", required=True)
parser.add_argument("--identity")
parser.add_argument("--output", default="release/spec.yaml")
args = parser.parse_args()
if not re.fullmatch(r"[a-z0-9_.-]+/[a-z0-9_.-]+", args.repository):
    parser.error("repository must be lowercase owner/name")
if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", args.tag):
    parser.error("tag must be vMAJOR.MINOR.PATCH")
identity = args.identity or f"https://github.com/{args.repository}/.github/workflows/release.yml@refs/tags/{args.tag}"
if not re.fullmatch(r"https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/\.github/workflows/release\.yml@refs/tags/v[0-9]+\.[0-9]+\.[0-9]+", identity):
    parser.error("invalid signing identity")
digests = []
for path in (args.player, args.referee):
    digest = json.loads(Path(path).read_text())["containerimage.digest"]
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest) or digest.endswith("0" * 64):
        parser.error("invalid pushed digest")
    digests.append(digest)
spec = Path("spec.yaml").read_text()
spec = re.sub(r"^# (?:Development|Release-source) spec.*\n", "# Generated from a tagged, signed release.\n", spec)
spec = re.sub(r"^version: .+$", f"version: {args.tag[1:]}", spec, flags=re.M)
spec = re.sub(r"(?m)^(\s*ref: )ghcr\.io/[^\s]+-player$", lambda m: m[1] + f"ghcr.io/{args.repository}-player", spec)
spec = re.sub(r"(?m)^(\s*ref: )ghcr\.io/[^\s]+-referee$", lambda m: m[1] + f"ghcr.io/{args.repository}-referee", spec)
pattern = r"(?m)^(\s*digest: )sha256:[0-9a-f]{64}$"
if len(re.findall(pattern, spec)) != 2:
    parser.error("expected two image digests")
values = iter(digests)
spec = re.sub(pattern, lambda m: m[1] + next(values), spec)
spec = re.sub(r"(?m)^(\s*cosign_identity: ).+$", lambda m: m[1] + identity, spec)
if "owner-pending" in spec or "sha256:" + "0" * 64 in spec:
    parser.error("unresolved release fields")
output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(spec)
for path in ("input.schema.json",):
    (output.parent / path).write_bytes(Path(path).read_bytes())
