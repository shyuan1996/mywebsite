import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { resolve, extname, sep } from "node:path";
const argPort = process.argv.indexOf("--port");
const previewPort =
  process.env.PORT || (argPort >= 0 ? process.argv[argPort + 1] : 5173);
const root = resolve(import.meta.dirname, "..");
const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".webp": "image/webp",
  ".jpg": "image/jpeg",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
};
createServer(async (req, res) => {
  try {
    let name = decodeURIComponent(
      new URL(req.url, "http://localhost").pathname,
    );
    if (name === "/__preview-submit") {
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(
        '<p>這是設計預覽，表單沒有送出。</p><a href="/contact.html">返回聯絡頁</a>',
      );
      return;
    }
    if (name === "/") name = "/index.html";
    if (name === "/review") name = "/scripts/review.html";
    if (name.split("/").some((s) => s.startsWith("."))) throw Error("Hidden");
    let path = resolve(root, "." + name);
    if (!path.startsWith(root + sep)) throw Error("Invalid path");
    if (!extname(path)) path += ".html";
    if (!(await stat(path)).isFile()) throw Error("Not a file");
    let data = await readFile(path);
    if (extname(path) === ".html")
      data = Buffer.from(
        data
          .toString()
          .replace(
            'action="https://formspree.io/f/mvgwrvwv"',
            'action="/__preview-submit"',
          )
          .replace(
            "</head>",
            '<meta name="shyuan-preview" content="true"></head>',
          ),
      );
    res.writeHead(200, {
      "Content-Type": types[extname(path)] || "application/octet-stream",
      "Cache-Control": "no-cache",
      "X-Content-Type-Options": "nosniff",
    });
    res.end(data);
  } catch {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("找不到頁面");
  }
}).listen(Number(previewPort), "0.0.0.0", () =>
  console.log("Shyuan design preview ready"),
);
