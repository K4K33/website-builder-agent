"""Fail-closed owner-preview publishing check for source-faithful Kaurivo prototypes.

Owner preview is *not* sales approval and does not imply a 9.5/10 score.
This gate prevents a ZIP/half-rendered source from being published with a URL.
"""
from __future__ import annotations
import json,os,re,sys,subprocess
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs'/'kaurivo'/'owner-previews'
EVIDENCE=ROOT/'data'/'owner_previews'
PREFIX='website-builder-agent/website-builder-agent/docs/kaurivo/owner-previews/'


def check_preview(slug:str)->list[str]:
    problems=[];folder=BASE/slug
    manifest=EVIDENCE/(slug+'.json')
    if not manifest.exists():return ['Missing independently captured source/brand evidence manifest']
    try:data=json.loads(manifest.read_text(encoding='utf-8'))
    except (ValueError,OSError):return ['Invalid evidence JSON']
    required=('schema_version','stage','status','company_name','verified_at','source_url','source_pages',
              'verified_facts','brand_provenance','source_inventory','release_routes','outreach_authorized')
    if any(key not in data for key in required):problems.append('Evidence manifest missing mandatory fields')
    if data.get('stage')!='owner_preview' or data.get('outreach_authorized') is not False:
        problems.append('Preview may not impersonate sales authorization')
    name=str(data.get('company_name') or '').strip()
    if len(name)<7 or not data.get('source_url','').startswith('https://'):
        problems.append('Missing official company/source identity')
    source=data.get('source_pages') or []
    if not isinstance(source,list) or len(source)<2 or any(not str(s).startswith('https://') for s in source):
        problems.append('At least 2 verified original route references required')
    facts=data.get('verified_facts') or {}
    if any(not facts.get(k) for k in ('phone','email','street','hours','service_exclusions')):
        problems.append('Missing critical current company facts')
    brand=data.get('brand_provenance') or {}
    if not brand.get('retained_signature') or not brand.get('original_image_reuse_status'):
        problems.append('Brand and photo rights inventory missing')
    declared=set(data.get('release_routes') or [])
    found={p.relative_to(folder).as_posix() for p in folder.rglob('*.html')}
    if found!=declared or len(found)<2 or 'index.html' not in found:
        problems.append('Actual multi-page routes differ from manifest')
    cssfile=folder/'assets'/'site.css'
    jsfile=folder/'assets'/'site.js'
    if not cssfile.is_file() or not jsfile.is_file():return problems+['Real local CSS/JS missing']
    css=cssfile.read_text(encoding='utf-8')
    if not re.search(r'#[0-9a-f]{6}',css,re.I) or '#d90029' not in css.lower():
        problems.append('Source brand color not explicitly retained')
    if re.search(r'https?://|//commons\.',css,re.I):
        problems.append('Remote styling/media dependency still present')
    for route in found:
        p=folder/route;soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
        prefix=p.parent
        title=soup.title.get_text(' ',strip=True) if soup.title else ''
        if name not in title or len(title)>80 or not title.strip() or 'Kaurivo Demo' in title:
            problems.append(f'{route}: inaccurate or non-premium browser title')
        if not soup.html or soup.html.get('lang') not in ('fi','sv','en'):
            problems.append(f'{route}: missing exact language')
        meta=soup.select_one('meta[name="description"]')
        if not meta or len(meta.get('content','').strip())<50:
            problems.append(f'{route}: missing meaningful SEO description')
        if not soup.select_one('meta[name="robots"][content*="noindex"]'):
            problems.append(f'{route}: owner review must not be indexed')
        if len(soup.select('main h1'))!=1:problems.append(f'{route}: one meaningful main H1 required')
        if not soup.select_one('.demo-band') or 'virallinen' not in soup.select_one('.demo-band').get_text(' ',strip=True):
            problems.append(f'{route}: non-official demo disclaimer missing')
        if soup.select_one('header img,header svg.brand-logo'):
            problems.append(f'{route}: unverified company logo graphic')
        icon=soup.select_one('link[rel~=icon]')
        if not icon or icon.get('data-kaurivo-neutral-demo-icon')!='true':
            problems.append(f'{route}: licensed logo or explicitly neutral placeholder favicon required')
        if soup.find('form'):problems.append(f'{route}: unproven contact form destination')
        if not soup.select_one('a[href="tel:+3589302113"]'):
            problems.append(f'{route}: verified telephone action missing')
        for el in soup.select('img[src],script[src],link[rel~=stylesheet][href],link[rel~=icon][href]'):
            link=el.get('src') or el.get('href') or ''
            if link.startswith(('https:','http:','//','data:')):
                problems.append(f'{route}: external or inline dependency {link[:80]}')
                continue
            target=(prefix/link).resolve()
            if not target.is_relative_to(folder.resolve()) or not target.is_file():
                problems.append(f'{route}: missing locally deployed asset {link}')
            elif target.suffix=='.svg':
                try:ET.parse(target)
                except ET.ParseError:problems.append(f'{route}: corrupted favicon/illustration SVG {link}')
        for el in soup.select('[style]'):
            value=el.get('style') or ''
            for ref in re.findall(r'url\([\'\"]?([^\)\'\"]+)',value):
                if ref.startswith(('https:','http:','//')):
                    problems.append(f'{route}: unstable external hero/background asset')
                else:
                    target=(prefix/ref).resolve()
                    if not target.is_relative_to(folder.resolve()) or not target.is_file():
                        problems.append(f'{route}: missing local background asset {ref}')
        for a in soup.select('a[href]'):
            href=a.get('href','')
            if href.startswith(('https://','mailto:','tel:','#')):continue
            target=(prefix/href.split('#')[0].split('?')[0]).resolve()
            if target.is_dir():target=target/'index.html'
            if not target.is_relative_to(folder.resolve()) or not target.is_file():
                problems.append(f'{route}: broken navigation {href}')
    texts=' '.join(BeautifulSoup((folder/p).read_text(encoding='utf-8'),'html.parser').get_text(' ',strip=True) for p in found)
    for fact in ('09 302 113','Heisitie 4','info@rasasenautohuolto.fi','08.00–17.00','ruostekorjauksia','kolarikorjauksia','Autofit'):
        if fact.casefold() not in texts.casefold():problems.append('Source fact omitted: '+fact)
    if 'https://www.rasasenautohuolto.fi/yhteystiedot.html' not in (folder/'yhteys/index.html').read_text(encoding='utf-8'):
        problems.append('Original working contact-form visitor journey not retained')
    return problems


def changed():
    before=os.getenv('BASE_SHA','');after=os.getenv('HEAD_SHA','')
    if not before or not after:raise RuntimeError('Missing commit bounds')
    files=subprocess.check_output(['git','diff','--name-only',before,after],cwd=ROOT,text=True).splitlines()
    slugs={p[len(PREFIX):].split('/')[0] for p in files if p.startswith(PREFIX) and '/' in p[len(PREFIX):]}
    return sorted(s for s in slugs if re.fullmatch(r'[a-z0-9-]+',s))

def main():
    failures=0
    for slug in changed():
        problems=check_preview(slug)
        if problems:
            failures+=1
            for problem in problems:print('BLOCK',slug,problem)
        else:print('SOURCE_BOUNDED_OWNER_PREVIEW_PASS',slug,'independent design approval still required for outreach')
    return min(failures,1)

if __name__=='__main__':sys.exit(main())