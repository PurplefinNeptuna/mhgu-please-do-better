from paths import MOD, SCRIPTS, FORGE, DEPS, PYTHON, CONTAINER_STORAGE, input_path
#!/usr/bin/env python3
"""Bound r15 log text against maintained Forge's fixed formatter buffer."""
import re
import please_do_better as recipe


def main():
    source=(recipe.RECIPE/'src/runtime.cpp').read_text()
    logger=(recipe.FORGE / 'source/forge/log.c').read_text()
    size=int(re.search(r'void forge_log\(.*?char buffer\[(\d+)\]',logger,re.S)[1])
    token=re.compile(r'%(?:[-+ #0]*[0-9]*(?:\.[0-9]+)?)(ll)?([duxXifeg])')
    formats=re.findall(r'forge_log_info\("([^"\n]*r15[^"\n]*)"',source)
    recipe.require(len(formats)==4,'Release must contain only startup and concise suppression formats')
    limits=[];checks=0
    for fmt in formats:
        bound=len(fmt)
        for m in token.finditer(fmt):
            wide,kind=m.groups()
            width=16 if wide else 16 if kind in 'feg' else 11 if kind in 'di' else 8 if kind in 'xX' else 10
            bound+=width-len(m[0])
        recipe.require('%' not in token.sub('',fmt),'Unbounded/unsupported trace format')
        recipe.require(bound+7<size,'Trace could exceed Forge buffer: '+fmt);checks+=1
        for fp in (-3.4028234663852886e38,3.4028234663852886e38,float('inf'),float('nan')):
            args=[]
            for m in token.finditer(fmt):
                wide,kind=m.groups()
                args.append(fp if kind in 'feg' else -2**31 if kind in 'di' else 2**64-1 if wide else 2**32-1)
            rendered=fmt.replace('llx','x').replace('llu','u')%tuple(args)
            recipe.require(len(rendered.encode())+7<size,'Worst-value formatted trace exceeds Forge buffer');checks+=1
        limits.append({'format':fmt,'maximum_bytes_with_prefix':bound+7})
    recipe.write_json(recipe.OUT/'log-tests.json',{'checks':checks,'forge_buffer_bytes':size,
        'maximum_bound_bytes':max(x['maximum_bytes_with_prefix'] for x in limits),'formats':limits,
        'source_sha256':recipe.sha(source.encode()),'forge_log_source_sha256':recipe.sha(logger.encode()),
        'limits':['Text bounds only; compiled ARM variadic fixtures validate argument ABI','R14 visible Eden marker accepted; r15 logging-only cleanup not gameplay retested']})
    print(f'PASS: {checks} log text bounds; {len(formats)} formats fit Forge {size}-byte buffer')


if __name__=='__main__':main()
