"""Optional public-source page change monitor. No incident or user data is collected.
Changes are signals for human review, not legal conclusions."""
import json, hashlib, urllib.request, re, datetime, pathlib
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parent
SOURCES={
 'PACE': 'https://www.legislation.gov.uk/ukpga/1984/60/contents',
 'Code A': 'https://www.gov.uk/government/publications/pace-code-a-december-2023/pace-code-a-2023-accessible',
 'Code C': 'https://www.gov.uk/government/publications/pace-code-c-2023/pace-code-c-2023-accessible',
 'Police Reform Act s.50': 'https://www.legislation.gov.uk/ukpga/2002/30/section/50',
 'Dispersal powers': 'https://www.legislation.gov.uk/ukpga/2014/12/section/35',
 'Terrorism Act s.43': 'https://www.legislation.gov.uk/ukpga/2000/11/section/43',
 'Crime and Policing Act 2026': 'https://www.legislation.gov.uk/ukpga/2026/20/contents',
 'PACE codes index': 'https://www.gov.uk/guidance/police-and-criminal-evidence-act-1984-pace-codes-of-practice',
 'IOPC reviews': 'https://www.policeconduct.gov.uk/complaints/reviews-and-appeals',
}
class Visible(HTMLParser):
 def __init__(self): super().__init__(); self.skip=0; self.parts=[]
 def handle_starttag(self,t,a):
  if t in ('script','style','noscript'): self.skip+=1
 def handle_endtag(self,t):
  if t in ('script','style','noscript') and self.skip:self.skip-=1
 def handle_data(self,s):
  if not self.skip:self.parts.append(s)
path=ROOT/'updates.json'; old=json.loads(path.read_text()) if path.exists() else {}; prev={x['name']:x for x in old.get('sources',[])}; rows=[]
for name,url in SOURCES.items():
 previous=prev.get(name,{}); baseline=previous.get('baseline'); last=previous.get('hash'); row={'name':name,'url':url,'baseline':baseline,'hash':last}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'CivicGround UK educational source monitor/4.0 (public pages only)'})
  with urllib.request.urlopen(req,timeout=25) as r:
   raw=r.read(8_000_000).decode('utf-8','replace')
  v=Visible();v.feed(raw); content=re.sub(r'\s+',' ',' '.join(v.parts)).strip()
  if len(content)<500 or 'checking your browser' in content.lower() or 'captcha' in content.lower()[:500]:raise ValueError('Unexpected or blocked page')
  digest=hashlib.sha256(content.encode()).hexdigest(); row.update(hash=digest,baseline=baseline or digest,status='Baseline captured; no legal review performed' if not baseline else ('Page differs from baseline — human review needed' if digest!=baseline else 'Page matches baseline — not proof law is unchanged'))
 except Exception as e:row['status']='Check failed — '+type(e).__name__+'; open official source manually'
 rows.append(row)
path.write_text(json.dumps({'generated':datetime.datetime.now(datetime.timezone.utc).isoformat(),'note':'Page-text comparison only; amendments, commencement, judicial developments and false positives require human review.','sources':rows},indent=2)+'\n')
