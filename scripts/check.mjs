import { readFile, stat } from "node:fs/promises";
import { resolve, join } from "node:path";
import assert from "node:assert/strict";
const root = resolve(import.meta.dirname, "..");
const pages = ["index", "about", "services", "portfolio", "contact"];
const html = Object.fromEntries(
  await Promise.all(
    pages.map(async (p) => [
      p,
      await readFile(join(root, p + ".html"), "utf8"),
    ]),
  ),
);
let links = 0;
for (const [page, source] of Object.entries(html)) {
  assert.equal(
    (source.match(/<h1[ >]/g) || []).length,
    1,
    `${page}: one main heading`,
  );
  assert(source.includes('lang="zh-Hant-TW"'), `${page}: language`);
  assert(source.includes('rel="canonical"'), `${page}: canonical`);
  assert(
    !/AIRTABLE_TOKEN\s*=\s*['"]|pat[A-Za-z0-9]{12,}/.test(source),
    `${page}: exposed credential`,
  );
  for (const schema of source.matchAll(
    /<script type="application\/ld\+json">([\s\S]*?)<\/script>/g,
  ))
    JSON.parse(schema[1]);
  for (const match of source.matchAll(/(?:src|href)="([^"]+)"/g)) {
    const raw = match[1];
    if (/^(https?:|mailto:|tel:|line:)/.test(raw)) continue;
    const [pathname, fragment] = raw.split("#");
    const path = pathname.split("?")[0] || page + ".html";
    assert((await stat(join(root, path))).isFile(), `${page}: missing ${path}`);
    if (fragment && path.endsWith(".html")) {
      const target = await readFile(join(root, path), "utf8");
      assert(
        target.includes(`id="${fragment}"`),
        `${page}: missing #${fragment}`,
      );
    }
    links++;
  }
}
const projects = JSON.parse(
  await readFile(join(root, "data/projects.json"), "utf8"),
);
assert.equal(
  new Set(projects.map((p) => p.id)).size,
  projects.length,
  "Unique archive ids",
);
let images = 0;
for (const project of projects) {
  assert(
    project.name && project.category && project.images.length,
    "Archive fields",
  );
  for (const path of project.images) {
    assert((await stat(join(root, path))).size > 0, `Missing ${path}`);
    images++;
  }
}
const js = await readFile(join(root, "js/main.js"), "utf8");
assert(!/Bearer |pat[A-Za-z0-9]{12,}/.test(js), "No client credentials");
assert(js.includes("textContent"), "Dynamic content uses text nodes");
console.log(
  `PASS: 5 pages, ${links} local references, ${projects.length} published projects, ${images} photos; metadata and credential checks passed.`,
);
