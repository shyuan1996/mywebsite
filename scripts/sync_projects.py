"""Export published Airtable projects without shipping credentials to the browser.
Requires Python 3.10+ and Pillow. Supply AIRTABLE_TOKEN via the environment.
Downloads a complete snapshot before replacing any existing public archive.
"""
import concurrent.futures
import io
import json
import os
import shutil
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('AIRTABLE_BASE_ID', 'appWtvyd8MgJ3cmrW')
TABLE = os.environ.get('AIRTABLE_TABLE', 'Table 1')
TOKEN = os.environ.get('AIRTABLE_TOKEN')
if not TOKEN:
    raise SystemExit('Set AIRTABLE_TOKEN in the environment. Never add it to the repository.')
query = {'filterByFormula': "{狀態 (Status)}='發布 (Published)'"}
records = []
while True:
    url = f'https://api.airtable.com/v0/{urllib.parse.quote(BASE)}/{urllib.parse.quote(TABLE)}?' + urllib.parse.urlencode(query)
    request = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + TOKEN})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    records.extend(data.get('records', []))
    if not data.get('offset'):
        break
    query['offset'] = data['offset']
records.sort(key=lambda r: r['createdTime'], reverse=True)
with tempfile.TemporaryDirectory(prefix='shyuan-sync-', dir=ROOT) as staging:
    staging = Path(staging)
    jobs, projects = [], []
    for record in records:
        fields = record['fields']
        attachments = fields.get('專案主圖 (MainImage)', [])
        if not fields.get('專案名稱 (ProjectName)') or not attachments:
            continue
        images = []
        for index, attachment in enumerate(attachments, 1):
            name = f'{record["id"]}-{index}.webp'
            url = attachment.get('thumbnails', {}).get('large', {}).get('url', attachment['url'])
            jobs.append((url, staging / name))
            images.append('images/projects/' + name)
        projects.append({'id': record['id'], 'name': fields['專案名稱 (ProjectName)'],
                         'category': fields.get('分類 (Category)', '客製品'),
                         'description': fields.get('專案簡介 (Description)', ''), 'images': images})
    if not projects:
        raise SystemExit('No published projects returned; existing archive was preserved.')
    def download(job):
        url, target = job
        with urllib.request.urlopen(url, timeout=30) as response:
            image = ImageOps.exif_transpose(Image.open(io.BytesIO(response.read()))).convert('RGB')
        image.thumbnail((1800, 1800))
        image.save(target, 'WEBP', quality=82, method=4)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as workers:
        list(workers.map(download, jobs))
    archive = ROOT / 'images/projects'
    archive.mkdir(parents=True, exist_ok=True)
    for _, path in jobs:
        shutil.copy2(path, archive / path.name)
    (ROOT / 'data').mkdir(exist_ok=True)
    snapshot = staging / 'projects.json'
    snapshot.write_text(json.dumps(projects, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(snapshot, ROOT / 'data/projects.json')
    # Kept images also support hand-curated home-page selections. Do not delete them here.
print(f'Exported {len(projects)} published projects and {len(jobs)} photos. Review before publishing.')
