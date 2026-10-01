"""Export published Airtable projects; only changed photos are downloaded.
Failed downloads preserve the previous snapshot. AIRTABLE_TOKEN stays private.
"""
import argparse
import concurrent.futures
import hashlib
import io
import json
import os
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = {"edge": 1800, "quality": 82, "method": 4, "format": "WEBP"}
MANIFEST = "data/sync-image-manifest.json"


def request_bytes(url, token=None, limit=50 * 1024 * 1024):
    headers = {"User-Agent": "Shyuan-Project-Sync/1.0"}
    if token:
        headers["Authorization"] = "Bearer " + token
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45) as response:
                body = response.read(limit + 1)
            if len(body) > limit:
                raise ValueError("Response exceeded the download size limit")
            return body
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise RuntimeError(f"Remote request failed (HTTP {error.code})") from None
            time.sleep(30 if error.code == 429 else 2 ** (attempt + 1))
        except urllib.error.URLError:
            if attempt == 2:
                raise RuntimeError("Network request failed; retry the workflow") from None
            time.sleep(2 ** (attempt + 1))


def fetch_records(token, base, table, fetch=request_bytes):
    query = {"filterByFormula": "{狀態 (Status)}='發布 (Published)'", "pageSize": 100}
    records, seen_offsets = [], set()
    while True:
        url = (f"https://api.airtable.com/v0/{urllib.parse.quote(base, safe='')}/"
               f"{urllib.parse.quote(table, safe='')}?" + urllib.parse.urlencode(query))
        data = json.loads(fetch(url, token=token))
        if not isinstance(data.get("records"), list):
            raise ValueError("Airtable did not return a records array")
        records.extend(data["records"])
        offset = data.get("offset")
        if not offset:
            return records
        if offset in seen_offsets:
            raise ValueError("Airtable returned a repeated pagination offset")
        seen_offsets.add(offset)
        query["offset"] = offset


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download_image(url, target):
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or not (host.endswith(".airtableusercontent.com") or host.endswith(".airtable.com")):
        raise ValueError("Expected an Airtable HTTPS attachment URL")
    with Image.open(io.BytesIO(request_bytes(url))) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((SETTINGS["edge"], SETTINGS["edge"]))
        image.save(target, SETTINGS["format"], quality=SETTINGS["quality"], method=SETTINGS["method"])


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def replace_if_changed(path, data):
    if path.exists() and path.read_bytes() == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as file:
        file.write(data)
        temporary = Path(file.name)
    os.replace(temporary, path)
    return True


def html_image_references(root):
    paths = set()
    for page in root.glob("*.html"):
        if page.name != "offline-preview.html":
            paths.update(re.findall(r'''(?:src|href)=["'](images/projects/[^"'?#]+)''', page.read_text()))
    return paths


def sync_projects(root, records, allow_empty=False, downloader=download_image):
    root = Path(root)
    cache_path = root / MANIFEST
    old_cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    cached = old_cache.get("images", {}) if old_cache.get("settings") == SETTINGS else {}
    ids, projects, entries, jobs = set(), [], {}, {}
    skipped = 0
    records = sorted(records, key=lambda record: (record.get("createdTime", ""), record["id"]), reverse=True)
    with tempfile.TemporaryDirectory(prefix="shyuan-sync-", dir=root) as staging_dir:
        staging = Path(staging_dir)
        for record in records:
            record_id = record["id"]
            if not re.fullmatch(r"rec[A-Za-z0-9]+", record_id) or record_id in ids:
                raise ValueError("Invalid or duplicate project record ID")
            ids.add(record_id)
            fields = record["fields"]
            if fields.get("狀態 (Status)") != "發布 (Published)":
                continue
            name, attachments = fields.get("專案名稱 (ProjectName)"), fields.get("專案主圖 (MainImage)", [])
            if not isinstance(name, str) or not name.strip() or not attachments:
                skipped += 1
                continue
            image_paths = []
            for attachment in attachments:
                attachment_id = attachment["id"]
                if not re.fullmatch(r"att[A-Za-z0-9]+", attachment_id):
                    raise ValueError("Invalid attachment ID")
                identity = {"id": attachment_id, "size": attachment.get("size"), "width": attachment.get("width"),
                            "height": attachment.get("height"), "settings": SETTINGS}
                fingerprint = hashlib.sha256(json_bytes(identity)).hexdigest()
                path = f"images/projects/{record_id}-{attachment_id}-{fingerprint[:12]}.webp"
                image_paths.append(path)
                entry = {"attachment_id": attachment_id, "fingerprint": fingerprint}
                previous, local_file = cached.get(path, {}), root / path
                if (previous.get("fingerprint") == fingerprint and local_file.is_file()
                        and previous.get("sha256") == digest(local_file)):
                    entry["sha256"] = previous["sha256"]
                else:
                    jobs[path] = (attachment["url"], staging / Path(path).name)
                entries[path] = entry
            category, description = fields.get("分類 (Category)") or "客製品", fields.get("專案簡介 (Description)") or ""
            if not isinstance(category, str) or not isinstance(description, str):
                raise ValueError("Project category and description must be text")
            projects.append({"id": record_id, "name": name.strip(), "category": category,
                             "description": description, "images": image_paths})
        if not projects and not allow_empty:
            raise ValueError("No published projects. Snapshot preserved; allow-empty is required to withdraw everything")
        # No existing public files are touched until all required downloads succeed.
        def process(item):
            path, (url, target) = item
            downloader(url, target)
            with Image.open(target) as image:
                image.verify()
            if target.stat().st_size == 0:
                raise ValueError("An attachment produced an empty image")
            return path, digest(target)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as workers:
            for path, sha in workers.map(process, jobs.items()):
                entries[path]["sha256"] = sha
        manifest = {"version": 1, "settings": SETTINGS, "images": dict(sorted(entries.items()))}
        changed = False
        for path, (_, target) in jobs.items():
            destination = root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists() or digest(destination) != entries[path]["sha256"]:
                os.replace(target, destination)
                changed = True
        changed |= replace_if_changed(root / "data/projects.json", json_bytes(projects))
        changed |= replace_if_changed(cache_path, json_bytes(manifest))
        keep, removed = set(entries) | html_image_references(root), 0
        for file in (root / "images/projects").glob("*.webp"):
            managed = re.fullmatch(r"rec[A-Za-z0-9]+-(?:\d+|att[A-Za-z0-9]+-[0-9a-f]{12})\.webp", file.name)
            if managed and file.relative_to(root).as_posix() not in keep:
                file.unlink()
                removed += 1
                changed = True
    return {"projects": len(projects), "photos": sum(len(p["images"]) for p in projects), "downloaded": len(jobs),
            "reused": len(entries) - len(jobs), "removed": removed, "skipped": skipped, "changed": bool(changed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args()
    token = os.environ.get("AIRTABLE_TOKEN")
    if not token:
        raise SystemExit("Missing AIRTABLE_TOKEN. Add it under GitHub Settings > Secrets and variables > Actions")
    try:
        records = fetch_records(token, os.environ.get("AIRTABLE_BASE_ID") or "appWtvyd8MgJ3cmrW",
                                os.environ.get("AIRTABLE_TABLE") or "Table 1")
        report = sync_projects(ROOT, records, allow_empty=args.allow_empty)
        replace_if_changed(ROOT / ".sync-report.json", json_bytes(report))
        print(f"Projects: {report['projects']}; photos: {report['photos']}; downloaded: {report['downloaded']}; "
              f"reused: {report['reused']}; skipped incomplete records: {report['skipped']}")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a") as file:
                file.write(f"## Airtable 作品同步\n\n已發布作品：{report['projects']} 件；照片：{report['photos']} 張。\n\n"
                           f"下載或修復：{report['downloaded']} 張；沿用：{report['reused']} 張；清理未使用副本：{report['removed']} 張。\n\n"
                           f"缺少名稱或照片而略過：{report['skipped']} 件。\n\n")
    except Exception as error:
        safe = str(error) if isinstance(error, (ValueError, RuntimeError)) else type(error).__name__
        raise SystemExit("Synchronization failed; no deployment will run. " + safe) from None


if __name__ == "__main__":
    main()
