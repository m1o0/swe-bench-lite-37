"""Measure Docker Hub blob throughput from WSL, optionally through a proxy.

Usage:
  python3 speedtest_dockerhub.py [proxy_url] [repo] [tag] [max_mb]
Defaults: no proxy, library/python, 3.9-slim, 60 MB.
Runs inside WSL (the network namespace that matters for dockerd).
"""

import json
import sys
import time
import urllib.request

proxy = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else None
repo = sys.argv[2] if len(sys.argv) > 2 else "library/python"
tag = sys.argv[3] if len(sys.argv) > 3 else "3.9-slim"
max_mb = float(sys.argv[4]) if len(sys.argv) > 4 else 60.0

handlers = []
if proxy:
    handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
opener = urllib.request.build_opener(*handlers)

token_url = (
    "https://auth.docker.io/token?service=registry.docker.io&scope=repository:%s:pull" % repo
)
token = json.load(opener.open(token_url, timeout=30))["token"]

req = urllib.request.Request(
    "https://registry-1.docker.io/v2/%s/manifests/%s" % (repo, tag),
    headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.docker.distribution.manifest.v2+json",
    },
)
manifest = json.load(opener.open(req, timeout=30))

if "manifests" in manifest:  # multi-arch index: resolve linux/amd64 first
    digest = None
    for entry in manifest["manifests"]:
        platform = entry.get("platform") or {}
        if platform.get("architecture") == "amd64" and platform.get("os") == "linux":
            digest = entry["digest"]
            break
    if digest is None:
        digest = manifest["manifests"][0]["digest"]
    req = urllib.request.Request(
        "https://registry-1.docker.io/v2/%s/manifests/%s" % (repo, digest),
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.docker.distribution.manifest.v2+json",
        },
    )
    manifest = json.load(opener.open(req, timeout=30))

layer = max(manifest["layers"], key=lambda item: item["size"])

blob_req = urllib.request.Request(
    "https://registry-1.docker.io/v2/%s/blobs/%s" % (repo, layer["digest"]),
    headers={"Authorization": "Bearer " + token},
)

limit = int(max_mb * 1024 * 1024)
start = time.time()
got = 0
with opener.open(blob_req, timeout=60) as response:
    while got < limit:
        chunk = response.read(1 << 20)
        if not chunk:
            break
        got += len(chunk)
elapsed = time.time() - start

print(
    "proxy=%s repo=%s tag=%s layer_size=%.1fMB downloaded=%.1fMB elapsed=%.1fs speed=%.2f MB/s"
    % (
        proxy or "(direct)",
        repo,
        tag,
        layer["size"] / 1e6,
        got / 1e6,
        elapsed,
        got / elapsed / 1e6 if elapsed else 0.0,
    )
)
