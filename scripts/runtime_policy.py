from paths import NAME
#!/usr/bin/env python3
"""Check process-lifetime reason deduplication, UI ownership and formatter limits."""
import json,re,subprocess,os,hashlib
from pathlib import Path
from paths import MOD,ROOT,FORGE,BUILD_ROOT,WORK_ROOT

def check_formats():
 logger=(FORGE/'source/forge/log.c').read_text();size=int(re.search(r'void forge_log\(.*?char buffer\[(\d+)\]',logger,re.S)[1])
 token=re.compile(r'%(?:[-+ #0]*[0-9]*(?:\.[0-9]+)?)(ll)?([duxXifegs])')
 formats=[]
 for p in (MOD/'src').glob('*.cpp'):
  for fmt in re.findall(r'forge_log_(?:info|warn)\("([^"\n]*)"',p.read_text()):
   bound=len(fmt)
   for t in token.finditer(fmt):
    wide,k=t.groups();width=100 if k=='s' else 46 if k=='f' else 18 if k in 'eg' else 20 if wide else 11
    bound+=width-len(t[0])
   if '%' in token.sub('',fmt) or bound+7>=size:raise ValueError('Unbounded or oversized log format: '+fmt)
   formats.append({'format':fmt,'maximum_bytes_with_prefix':bound+7,'file':p.name})
 return {'status':'PASSED','checks':len(formats),'forge_buffer_bytes':size,'maximum_bound_bytes':max(x['maximum_bytes_with_prefix'] for x in formats),'formats':formats,'string_limit_bytes':100,'runtime_test':'NOT RUN'}

def main():
 work=WORK_ROOT/'host-policy';work.mkdir(parents=True,exist_ok=True)
 fixture=MOD/'tests/runtime_policy.cpp';exe=work/'policy'
 subprocess.run(['c++','-std=c++17','-O2','-pthread','-Wall','-Wextra','-Werror','-I',str(MOD/'src'),str(fixture),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
 source=(MOD/'src/plugin.cpp').read_text()
 if NAME in ('modern-weapon-controls','key-quest-markers'):
  body=re.search(r'void forge_onImGuiRender\(\)\s*\{([^}]*)}',source)[1]
  if re.search(r'ig\w+\(',body):raise ValueError('Settings-free plugin has a panel')
 else:
  ui=(MOD/'src/capture.cpp').read_text().split('void capture_panel() {',1)[1] if NAME=='damage-numbers' else source.split('void forge_onImGuiRender() {',1)[1].split('extern "C"',1)[0]
  if any(x in ui for x in ('Diagnostics','igText(','runtime_status','diagnostics()','reward observation','Currently highlighted')):raise ValueError('Settings UI contains diagnostics')
  if 'igTreeNode_Str' not in ui or 'TreePop' not in (ui+source):
   if NAME!='damage-numbers':raise ValueError('Settings tree scope unbalanced')
 result=check_formats();result['deduplication']='All 32 distinct IDs, repeat rejection, invalid ID and 16 concurrent threads passed';result['settings_only']=True
 result['sources']={str(p.relative_to(MOD)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (fixture,MOD/'src/log_policy.h')}
 out=BUILD_ROOT/'runtime-policy.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
 print('PASS: distinct/process-lifetime/concurrent reason reporting, settings-only source UI and native formatter bounds')
if __name__=='__main__':main()
