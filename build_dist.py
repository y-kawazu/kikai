from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST_ROOT = ROOT / "dist"
CLIENT_ROOT = DIST_ROOT / "client"
SERVER_ROOT = DIST_ROOT / "server"
OPENAI_ROOT = DIST_ROOT / ".openai"

WORKER_JS = """export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/") {
      url.pathname = "/index.html";
    }

    const assetResponse = await env.ASSETS.fetch(new Request(url.toString(), request));
    if (assetResponse.status !== 404) {
      if (url.pathname.endsWith(".html")) {
        const headers = new Headers(assetResponse.headers);
        headers.set("content-type", "text/html; charset=utf-8");
        headers.set("cache-control", "no-cache");
        return new Response(assetResponse.body, {
          status: assetResponse.status,
          headers,
        });
      }
      return assetResponse;
    }

    const fallbackUrl = new URL("/index.html", request.url);
    const fallbackResponse = await env.ASSETS.fetch(new Request(fallbackUrl.toString(), request));
    if (fallbackResponse.status !== 404) {
      const headers = new Headers(fallbackResponse.headers);
      headers.set("content-type", "text/html; charset=utf-8");
      headers.set("cache-control", "no-cache");
      return new Response(fallbackResponse.body, {
        status: 200,
        headers,
      });
    }

    return new Response("Not Found", { status: 404 });
  },
};
"""


def remove_readonly(func, path: str, _exc_info) -> None:
    """Retry removal after clearing attributes added by sync software."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, onexc=remove_readonly)


def copy_tree(source: Path, destination: Path) -> None:
    remove_tree(destination)
    shutil.copytree(source, destination)


def main() -> None:
    remove_tree(DIST_ROOT)

    CLIENT_ROOT.mkdir(parents=True, exist_ok=True)
    SERVER_ROOT.mkdir(parents=True, exist_ok=True)
    OPENAI_ROOT.mkdir(parents=True, exist_ok=True)

    shutil.copy2(ROOT / "index.html", CLIENT_ROOT / "index.html")
    copy_tree(ROOT / "写真", CLIENT_ROOT / "写真")
    shutil.copy2(ROOT / ".openai" / "hosting.json", OPENAI_ROOT / "hosting.json")

    (SERVER_ROOT / "index.js").write_text(WORKER_JS, encoding="utf-8")
    print(f"Prepared: {DIST_ROOT}")


if __name__ == "__main__":
    main()
