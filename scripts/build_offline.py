from pathlib import Path
import json,base64,re
from build_site import render_home
root=Path(__file__).resolve().parents[1]
mime={'.webp':'image/webp','.jpg':'image/jpeg','.png':'image/png','.woff2':'font/woff2'}
paths=list((root/'images/projects').glob('*.webp'))+list((root/'fonts').glob('*.woff2'))+[root/'images'/n for n in ['logo.png','company.webp','workshop.webp','counter.webp','social-cover.jpg']]
assets={str(p.relative_to(root)):'data:'+mime[p.suffix]+';base64,'+base64.b64encode(p.read_bytes()).decode() for p in paths}
data={'assets':assets,'pages':{p:(root/(p+'.html')).read_text() for p in ['index','about','services','portfolio','contact']},'css':(root/'style.css').read_text(),'fonts':(root/'fonts/fonts.css').read_text(),'script':(root/'js/main.js').read_text(),'projects':json.loads((root/'data/projects.json').read_text())}
data['pages']['index']=render_home(data['pages']['index'],data['projects'])
payload=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
chrome='''<!doctype html><html lang="zh-Hant-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>祥鉞｜離線設計預覽</title><style>*{box-sizing:border-box}body{margin:0;background:#dce0d4;color:#173c35;font:13px system-ui,sans-serif}header{padding:15px 22px;background:#173c35;color:#f2f1e9;display:flex;align-items:center;gap:20px;flex-wrap:wrap}header strong{font-size:14px}label{display:flex;align-items:center;gap:8px}select{padding:8px;color:#173c35;background:#f2f1e9;border:0;font:inherit}main{display:flex;justify-content:center;padding:24px;min-height:calc(100dvh - 72px)}iframe{width:100%;height:calc(100dvh - 120px);border:0;background:#f2f1e9;box-shadow:0 10px 35px #173c3526}p{margin:0;font-size:11px;opacity:.8}iframe.mobile{width:406px;height:860px;max-width:100%;border:8px solid #173c35;border-radius:30px}iframe.small{width:336px;height:766px;max-width:100%;border:8px solid #173c35;border-radius:26px}iframe.tablet{width:784px;height:1040px;max-width:100%;border:8px solid #173c35;border-radius:20px}@media(max-width:600px){main{padding:12px}header{gap:12px}}</style></head><body><header><div><strong>SHYUAN / 離線設計審閱</strong><p>尚未上線 · 表單不會送出 · 地圖需連網，其餘內容可離線檢查</p></div><label>頁面<select id="page"><option value="index">首頁</option><option value="about">關於祥鉞</option><option value="services">服務項目</option><option value="portfolio">精選作品</option><option value="contact">聯絡我們</option></select></label><label>尺寸<select id="size"><option value="desktop">桌面</option><option value="mobile">手機 390px</option><option value="small">小手機 320px</option><option value="tablet">平板 768px</option></select></label></header><main><iframe id="preview" title="祥鉞離線設計預覽"></iframe></main><script id="source" type="application/json">'''
script='''</script><script>
const bundle=JSON.parse(document.querySelector('#source').textContent),frame=document.querySelector('#preview'),page=document.querySelector('#page'),size=document.querySelector('#size');
document.querySelector('#source').remove();
const projects=bundle.projects.map(p=>({...p,images:p.images.map(path=>bundle.assets[path])}));
const fontCSS=bundle.fonts.replace(/url\\(\\.\\/([^)]*)\\)/g,(_,name)=>'url('+bundle.assets['fonts/'+name]+')');
function render(name,search='',hash='') {
 if(!bundle.pages[name])return;
 page.value=name;
 const doc=new DOMParser().parseFromString(bundle.pages[name],'text/html');
 doc.querySelectorAll('link[rel="stylesheet"],script[src]').forEach(el=>el.remove());
 doc.querySelectorAll('img[src],link[rel="icon"]').forEach(el=>{const attr=el.tagName==='IMG'?'src':'href';const path=el.getAttribute(attr);if(bundle.assets[path])el.setAttribute(attr,bundle.assets[path]);});
 const style=doc.createElement('style');style.textContent=fontCSS+'\\n'+bundle.css;doc.head.append(style);
 const meta=doc.createElement('meta');meta.name='shyuan-preview';meta.content='true';doc.head.append(meta);
 const form=doc.querySelector('form');if(form)form.action='#';
 const script=doc.createElement('script');
 const safeJSON=value=>JSON.stringify(value).replace(/</g,'\\\\u003c');
 const archive=name==='portfolio'?projects:projects.filter(p=>[...doc.querySelectorAll('[data-project]')].some(button=>button.dataset.project===p.id));
 script.textContent='window.SHYUAN_OFFLINE_PROJECTS='+safeJSON(archive)+';window.SHYUAN_OFFLINE_SERVICE='+safeJSON(new URLSearchParams(search).get('service'))+';\\n(()=>{\\n'+bundle.script.replace('function getProjects() {','function getProjects() { if(window.SHYUAN_OFFLINE_PROJECTS) return Promise.resolve(window.SHYUAN_OFFLINE_PROJECTS);').replace('new URLSearchParams(location.search).get("service")','window.SHYUAN_OFFLINE_SERVICE')+'\\n})();'+`\n document.addEventListener('click',e=>{const a=e.target.closest('a[href]');if(!a||a.target==='_blank')return;const href=a.getAttribute('href');if(href.startsWith('#')){e.preventDefault();document.getElementById(href.slice(1))?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});return;}const url=new URL(href,'https://preview.invalid/');if(url.origin==='https://preview.invalid'&&/\\.html$/.test(url.pathname)){e.preventDefault();parent.postMessage({type:'shyuan:page',page:url.pathname.split('/').pop().replace('.html',''),search:url.search,hash:url.hash},'*');}});`;
 if(hash) script.textContent+='\\nrequestAnimationFrame(()=>document.getElementById('+safeJSON(hash.slice(1))+')?.scrollIntoView());';
 doc.body.append(script);const frameDoc=frame.contentDocument;frameDoc.open();frameDoc.write('<!doctype html>'+doc.documentElement.outerHTML);frameDoc.close();
}
page.addEventListener('change',()=>render(page.value));size.addEventListener('change',()=>frame.className=size.value);
window.addEventListener('message',event=>{if(event.source===frame.contentWindow&&event.data?.type==='shyuan:page')render(event.data.page,event.data.search,event.data.hash);});
render('index');
</script></body></html>'''
(root/'offline-preview.html').write_text(chrome+payload+script)
print('Offline preview bytes:',(root/'offline-preview.html').stat().st_size)
