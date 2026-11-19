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


def check_source_limited_concept(slug:str,data:dict,folder:Path)->list[str]:
    """Fail-closed gate for a public owner-only concept when original is unreachable.

    This is NOT the source-preservation/quality gate used by publishable client
    work. Never call it when original source media/identity has been observed.
    Only release a visibly non-official study with independently cited public
    company identity, real contact actions, zero unproven branding and complete
    local pages. A separate real-browser CI run must also pass before merge.
    """
    from datetime import datetime,timezone
    errors=[]
    if (data.get('schema_version')!=2 or data.get('stage')!='owner_preview'
        or data.get('status')!='OWNER_PREVIEW_SOURCE_LIMITED_NO_CLIENT_APPROVAL'
        or data.get('outreach_authorized') is not False
        or data.get('marketing_eligible') is not False
        or data.get('client_approved') is not False
        or data.get('independent_quality_score') is not None):
        errors.append('Source-limited study must not claim review, rating or sales authorization')
    if data.get('official_site_access')!='unavailable_to_current_research':
        errors.append('Explicit and truthful original-site access limitation missing')
    if data.get('brand_verification')!='pending':
        errors.append('Missing explicit original-brand pending disclosure')
    if data.get('photos_verified_for_reuse') is not False:
        errors.append('Cannot treat inaccessible originals as licensed photo inventory')
    if data.get('cms_delivery_verified') is not False:
        errors.append('Static prototype must not claim verified client CMS')
    try:
        stamp=datetime.fromisoformat(str(data.get('verified_at') or '').replace('Z','+00:00'))
        if not stamp.tzinfo or stamp>datetime.now(timezone.utc):
            errors.append('Invalid verification timestamp')
    except ValueError:
        errors.append('Missing real source-check timestamp')
    name=str(data.get('company_name') or '').strip()
    business_id=str(data.get('company_business_id') or '').strip()
    if len(name)<7 or not re.fullmatch(r'\d{7}-\d',business_id):
        errors.append('Missing checked legal company identity')
    original=str(data.get('original_website_url') or '')
    if not original.startswith('https://'):
        errors.append('Cannot identify original website that was inaccessible')
    sources=data.get('source_pages')
    if not isinstance(sources,list) or len(sources)<2 or any(
        not isinstance(url,str) or not url.startswith('https://') for url in sources
    ):
        errors.append('Two independent public company sources are required')
    elif len({urlsplit(url).hostname for url in sources})<2:
        errors.append('Business identity needs two independent source domains')
    facts=data.get('verified_facts') or {}
    required=('phone','email','street','city','registered_industry')
    if any(not str(facts.get(k) or '').strip() for k in required):
        errors.append('Missing public-source factual contact, address or industry')
    if not str(facts.get('email') or '').count('@')==1:
        errors.append('Unusable source-verified email')
    brand=data.get('brand_provenance') or {}
    if (brand.get('identity_status')!='unverified'
        or brand.get('original_image_reuse_status')!='none_unverified_rights'
        or brand.get('new_mark_rights')!='no_new_logo'):
        errors.append('Cannot call a newly drawn visual identity the real business brand')
    routes=data.get('release_routes') or []
    found={p.relative_to(folder).as_posix() for p in folder.rglob('*.html')}
    if (not isinstance(routes,list) or len(routes)<2
        or len(routes)!=len(set(routes)) or set(routes)!=found
        or 'index.html' not in found):
        errors.append('All released multi-page routes must be present and declared')
    cssfile=folder/'assets/site.css'
    jsfile=folder/'assets/site.js'
    if not cssfile.is_file() or not jsfile.is_file():
        return errors+['Missing real locally deployed CSS/JS']
    css=cssfile.read_text(encoding='utf8')
    js=jsfile.read_text(encoding='utf8')
    if len(css)<3000 or len(js)<500 or 'prefers-reduced-motion' not in css:
        errors.append('Incomplete original desktop/mobile or reduced-motion presentation')
    if re.search(r'https?://|@import\b|url\(\s*["\']?//',css,re.I):
        errors.append('External styling/photography dependency forbidden')
    if 'data-email-builder' in js and (
        'mailto:' not in js or 'encodeURIComponent' not in js
    ):
        errors.append('Local email draft generator must be genuinely implemented')
    words=[]
    for route in found:
        p=folder/route
        soup=BeautifulSoup(p.read_text(encoding='utf8'),'html.parser')
        words.append(soup.get_text(' ',strip=True))
        if not soup.html or soup.html.get('lang') not in ('fi','sv','en'):
            errors.append(route+': language missing')
        title=soup.title.get_text(' ',strip=True) if soup.title else ''
        if name not in title or len(title)>90:
            errors.append(route+': wrong browser title / invented business identity')
        if not soup.select_one('meta[name="robots"][content*="noindex"]'):
            errors.append(route+': noindex required until client approval')
        meta=soup.select_one('meta[name="description"]')
        if not meta or len(str(meta.get('content') or ''))<50:
            errors.append(route+': missing meaningful description')
        if len(soup.select('main h1'))!=1:
            errors.append(route+': exactly one principal H1 required')
        ribbon=soup.select_one('.demo-band')
        if not ribbon or 'ei yrityksen virallinen sivu' not in ribbon.get_text(' ',strip=True).casefold():
            errors.append(route+': permanent bilingual non-official disclaimer required')
        if soup.select_one('header img,header svg.brand-logo'):
            errors.append(route+': cannot use a fabricated company logo')
        favicon=soup.select_one('link[rel~=icon]')
        if not favicon or favicon.get('data-kaurivo-neutral-demo-icon')!='true':
            errors.append(route+': neutral unbranded local favicon required')
        if not soup.select_one('a[href="tel:'+str(facts.get('phone') or '')+'"]'):
            errors.append(route+': verified direct phone action missing')
        if not soup.select_one('a[href="mailto:'+str(facts.get('email') or '')+'"]'):
            errors.append(route+': verified direct email action missing')
        if not soup.select_one('[data-set-lang="fi"]') or not soup.select_one('[data-set-lang="sv"]'):
            errors.append(route+': FI/SV controls required for bilingual source area')
        if (not soup.select_one('script[src]') or
            not soup.select_one('link[rel~=stylesheet][href]')):
            errors.append(route+': local CSS/JS not loaded')
        for item in soup.select('img[src],script[src],link[rel~=stylesheet][href],link[rel~=icon][href]'):
            path=(item.get('src') or item.get('href') or '')
            if path.startswith(('https:','http:','//','data:')):
                errors.append(route+': remote styling/media is not verified')
                continue
            target=(p.parent/path).resolve()
            if not target.is_relative_to(folder.resolve()) or not target.is_file():
                errors.append(route+': broken local asset '+path[:80])
            elif target.suffix=='.svg':
                try:ET.parse(target)
                except ET.ParseError:errors.append(route+': invalid SVG favicon')
        for link in soup.select('a[href]'):
            href=link.get('href') or ''
            if href.startswith(('https://','mailto:','tel:','#')):continue
            target=(p.parent/href.split('#')[0].split('?')[0]).resolve()
            if target.is_dir():target=target/'index.html'
            if not target.is_relative_to(folder.resolve()) or not target.is_file():
                errors.append(route+': broken navigation '+href)
        if soup.find('form'):
            forms=soup.find_all('form')
            if any('data-email-builder' not in form.attrs for form in forms):
                errors.append(route+': an unverified backend form is forbidden')
            if any(not form.find(string=re.compile(r'utkast|luonnos',re.I)) for form in forms):
                errors.append(route+': email-only draft must be clearly disclosed')
    text=' '.join(words).casefold()
    for fact in (name,str(facts.get('email') or ''),str(facts.get('street') or ''),
                 str(facts.get('business_id') or '')):
        if fact.strip() and fact.casefold() not in text:
            errors.append('Source fact omitted across site: '+fact[:60])
    if not re.search('ei yrityksen hyväksymä|inte godkänt av företaget',text):
        errors.append('Non-approval must remain visibly clear in document')
    if any(t in text for t in ('tutkitusti 5/5','verified customer reviews',
                              'varmistettu 9,5/10','100% kuljetustakuu')):
        errors.append('Fake customer satisfaction or performance claim')

    # If current registry classification contradicts older operator records,
    # neither source may be promoted into today's paid services. Uncertainty
    # must survive in the visible copy; a silent manifest flag is insufficient.
    conflict=data.get('historical_service_conflict')
    if conflict:
        if (not isinstance(conflict,dict) or
            conflict.get('status')!='conflicting_historic_industry_evidence' or
            conflict.get('independently_current_services_verified') is not False or
            data.get('registry_as_current_service') is not False or
            len(conflict.get('historical_sources') or [])<2):
            errors.append('Historical business conflict must block current-service inferences')
        for route in found:
            html=(folder/route).read_text(encoding='utf-8')
            soup=BeautifulSoup(html,'html.parser')
            visible=soup.get_text(' ',strip=True).casefold()
            forbidden=(
                'transportförfrågan','kuljetustiedustelu','förbered en transport',
                'avhämtningsort','noutopaikka','god(s)', 'tavara / arvioitu',
                'kuljetettava tavara','beställ transport','tilaa kuljetus',
                'rahtipalvelumme','våra frakttjänster'
            )
            for term in forbidden:
                if term in visible:
                    errors.append(route+': unsupported current service or freight-specific inquiry: '+term)
            if ('inte kunnat' not in visible and
                'ei ole voitu' not in visible and
                'ei ole vielä voitu' not in visible and
                'tulee vahvistaa' not in visible and
                'måste bekräftas' not in visible and
                'har inte kunnat' not in visible):
                errors.append(route+': uncertainty about present service offerings not visible')
        if facts.get('services') not in ([], None):
            errors.append('Current service list is unverified but populated')
    return errors


def check_preview(slug:str)->list[str]:
    problems=[];folder=BASE/slug
    manifest=EVIDENCE/(slug+'.json')
    if not manifest.exists():return ['Missing independently captured source/brand evidence manifest']
    try:data=json.loads(manifest.read_text(encoding='utf-8'))
    except (ValueError,OSError):return ['Invalid evidence JSON']
    if data.get('research_mode') == 'official_site_inaccessible_registry_concept':
        return check_source_limited_concept(slug,data,folder)
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
        if not soup.select_one('.demo-band b') or 'ei yrityksen virallinen sivu' not in soup.select_one('.demo-band b').get_text(' ',strip=True).casefold():
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