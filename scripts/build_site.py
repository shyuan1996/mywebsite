"""Build a public-only Pages artifact and refresh existing home-page selections."""
import html
import json
import re
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["index", "about", "services", "portfolio", "contact"]


def render_home(source, projects):
    by_id = {project["id"]: project for project in projects}

    def render_card(match):
        card = match.group(0)
        selected = re.search(r'data-project="([^"]+)"', card)
        if not selected:
            return card
        project = by_id.get(selected.group(1))
        if not project:
            return ""  # A withdrawn project must not remain in the public featured cards.
        name = html.escape(project["name"], quote=True)
        description = html.escape(project["description"] or project["category"], quote=True)
        card = re.sub(r'data-category="[^"]*"', lambda _: 'data-category="' + html.escape(project["category"], quote=True) + '"', card)
        card = re.sub(r'aria-label="[^"]*"', lambda _: 'aria-label="查看' + name + '相簿"', card, count=1)
        card = re.sub(r'src="[^"]*"', lambda _: 'src="' + html.escape(project["images"][0], quote=True) + '"', card, count=1)
        card = re.sub(r'alt="[^"]*"', lambda _: 'alt="' + name + '，' + description + '"', card, count=1)
        card = re.sub(r'(<span class="eyebrow">).*?(</span\s*>)', lambda m: m[1] + description + m[2], card, flags=re.S)
        card = re.sub(r'(<span class="image-count">).*?(</span\s*>)', lambda m: m[1] + f'{len(project["images"]):02d} PHOTOS' + m[2], card, flags=re.S)
        return re.sub(r'(<h3>).*?(</h3>)', lambda m: m[1] + name + m[2], card, flags=re.S)

    return re.sub(r'<article class="project-card"(?=[\s>]).*?</article>', render_card, source, flags=re.S)


def build_site(root=ROOT):
    root = Path(root).resolve()
    projects = json.loads((root / "data/projects.json").read_text())
    pages = {name + ".html": (root / (name + ".html")).read_text() for name in PAGES}
    pages["index.html"] = render_home(pages["index.html"], projects)
    images = {image for project in projects for image in project["images"]}
    for page in pages.values():
        images.update(path for path in re.findall(r'(?:src|href)="([^"]+)"', page) if path.startswith("images/"))
    with tempfile.TemporaryDirectory(prefix="shyuan-build-", dir=root) as directory:
        stage = Path(directory) / "site"
        stage.mkdir()

        def copy(path):
            source = (root / path).resolve()
            if not source.is_relative_to(root) or not source.is_file():
                raise ValueError("Missing or unsafe public asset: " + path)
            destination = stage / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        for name, content in pages.items():
            (stage / name).write_text(content)
        for path in ["style.css", "js/main.js", "data/projects.json", "CNAME", "sitemap.xml", "robots.txt"]:
            if (root / path).exists():
                copy(path)
        for font in (root / "fonts").iterdir():
            if font.is_file():
                copy(font.relative_to(root).as_posix())
        for path in sorted(images):
            copy(path)
        (stage / ".nojekyll").write_text("")
        destination = root / "_site"
        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(str(stage), destination)
    print(f"Public site built: {len(projects)} projects; {len(images)} image assets. No credentials, scripts or cache manifest included.")
    return destination


if __name__ == "__main__":
    build_site()
