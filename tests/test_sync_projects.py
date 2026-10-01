import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sync_projects import fetch_records, sync_projects, MANIFEST
from build_site import build_site, render_home


def attachment(identifier="attA"):
    return {"id": identifier, "size": 1000, "width": 32, "height": 24,
            "url": "https://v5.airtableusercontent.com/temporary/" + identifier}


def record(identifier="recA", photos=None, status="發布 (Published)"):
    return {"id": identifier, "createdTime": "2026-09-30T00:00:00Z", "fields": {
        "狀態 (Status)": status, "專案名稱 (ProjectName)": "工作檯",
        "分類 (Category)": "中彰投", "專案簡介 (Description)": "飲料店 / 台中",
        "專案主圖 (MainImage)": photos if photos is not None else [attachment()]}}


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.calls = []

    def download(self, url, target):
        self.calls.append(url)
        Image.new("RGB", (32, 24), "#173c35").save(target, "WEBP")

    def files(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file()}

    def sync(self, records, **options):
        return sync_projects(self.root, records, downloader=self.download, **options)

    def test_pagination_keeps_published_filter_and_authentication(self):
        calls = []
        def fetch(url, token=None):
            calls.append((parse_qs(urlparse(url).query), token))
            if len(calls) == 1:
                return json.dumps({"records": [record()], "offset": "next-page"}).encode()
            return json.dumps({"records": [record("recB")]}).encode()
        result = fetch_records("test-private-token", "appTest", "Table 1", fetch)
        self.assertEqual(len(result), 2)
        self.assertEqual(calls[1][0]["offset"], ["next-page"])
        self.assertEqual(calls[1][0]["filterByFormula"], ["{狀態 (Status)}='發布 (Published)'"])
        self.assertTrue(all(token == "test-private-token" for _, token in calls))

    def test_unchanged_photos_ignore_expiring_urls_and_text_changes_reuse_files(self):
        first = self.sync([record()])
        self.assertEqual(first["downloaded"], 1)
        before = self.files()
        changed_url = record()
        changed_url["fields"]["專案主圖 (MainImage)"][0]["url"] += "?fresh-signature=1"
        self.calls.clear()
        second = self.sync([changed_url])
        self.assertFalse(second["changed"])
        self.assertEqual(second["reused"], 1)
        self.assertEqual(self.calls, [])
        self.assertEqual(before, self.files())
        changed_url["fields"]["專案名稱 (ProjectName)"] = "新名稱"
        third = self.sync([changed_url])
        self.assertTrue(third["changed"])
        self.assertEqual(third["downloaded"], 0)
        self.assertNotIn("fresh-signature", (self.root / MANIFEST).read_text())

    def test_reordered_photos_are_reused_and_replaced_attachment_is_downloaded(self):
        original = record(photos=[attachment("attA"), attachment("attB")])
        self.sync([original])
        original["fields"]["專案主圖 (MainImage)"].reverse()
        report = self.sync([original])
        self.assertEqual(report["downloaded"], 0)
        original["fields"]["專案主圖 (MainImage)"][0] = attachment("attC")
        report = self.sync([original])
        self.assertEqual(report["downloaded"], 1)
        self.assertEqual(report["removed"], 1)

    def test_failed_download_preserves_previous_snapshot_and_all_images(self):
        self.sync([record()])
        before = self.files()
        def fail(url, target):
            raise RuntimeError("Simulated network failure")
        with self.assertRaises(RuntimeError):
            sync_projects(self.root, [record(photos=[attachment("attNew")])], downloader=fail)
        self.assertEqual(before, self.files())

    def test_drafts_are_excluded_and_empty_requires_deliberate_override(self):
        self.sync([record(), record("recDraft", status="草稿 (Draft)")])
        data = json.loads((self.root / "data/projects.json").read_text())
        self.assertEqual([p["id"] for p in data], ["recA"])
        before = self.files()
        with self.assertRaises(ValueError):
            self.sync([])
        self.assertEqual(before, self.files())
        report = self.sync([], allow_empty=True)
        self.assertEqual(report["projects"], 0)
        self.assertEqual(json.loads((self.root / "data/projects.json").read_text()), [])

    def test_corrupt_cache_is_repaired_and_curated_brand_image_is_preserved(self):
        self.sync([record()])
        file = next((self.root / "images/projects").glob("*.webp"))
        file.write_bytes(b"corrupt")
        self.assertEqual(self.sync([record()])["downloaded"], 1)
        pinned = self.root / "images/projects/recHero-3.webp"
        Image.new("RGB", (32, 24)).save(pinned, "WEBP")
        (self.root / "index.html").write_text('<img src="images/projects/recHero-3.webp">')
        self.sync([], allow_empty=True)
        self.assertTrue(pinned.exists())

    def test_duplicate_id_does_not_modify_public_files(self):
        self.sync([record()])
        before = self.files()
        with self.assertRaises(ValueError):
            self.sync([record(), copy.deepcopy(record())])
        self.assertEqual(before, self.files())


class PublishTests(unittest.TestCase):
    def test_home_selections_follow_published_record_and_escape_text(self):
        source = '''<article class="project-card" data-category="old"><button data-project="recA" aria-label="old"><img src="images/old.webp" alt="old"><span class="image-count">01 PHOTOS</span><span class="eyebrow">old</span><h3>old</h3></button></article>'''
        project = {"id": "recA", "name": '<script>alert("x")</script>', "description": "A & B",
                   "category": "中彰投", "images": ["images/projects/current.webp"]}
        rendered = render_home(source, [project])
        self.assertIn('src="images/projects/current.webp"', rendered)
        self.assertIn("A &amp; B", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertEqual(render_home(source, []), "")

    def test_artifact_whitelist_excludes_tokens_cache_and_developer_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ["index", "about", "services", "portfolio", "contact"]:
                (root / (name + ".html")).write_text('<img src="images/logo.png">')
            for folder in ["data", "js", "fonts", "images", "scripts", ".github"]:
                (root / folder).mkdir()
            (root / "data/projects.json").write_text("[]")
            (root / "data/sync-image-manifest.json").write_text("{}")
            (root / "images/logo.png").write_bytes(b"logo-fixture")
            (root / "style.css").write_text("")
            (root / "js/main.js").write_text("")
            (root / ".env").write_text("AIRTABLE_TOKEN=private-test-fixture")
            (root / "scripts/private.py").write_text("private-test-fixture")
            site = build_site(root)
            self.assertTrue((site / "index.html").exists())
            self.assertTrue((site / "images/logo.png").exists())
            self.assertFalse((site / ".env").exists())
            self.assertFalse((site / "scripts").exists())
            self.assertFalse((site / "data/sync-image-manifest.json").exists())
            self.assertNotIn("private-test-fixture", "".join(p.read_text() for p in site.rglob("*") if p.is_file()))


if __name__ == "__main__":
    unittest.main()
