"""Export a weight-free, path-sanitized static results publication."""
import _bootstrap
import argparse,gzip,hashlib,json,os,re,shutil,zipfile
from pathlib import Path
from markdown_it import MarkdownIt
from benchmark.util import ROOT,read_json,now
from dashboard.backend.app import summary
from dashboard.backend.output_history import readiness
from dashboard.backend.judging import judging

WEIGHTS={'.gguf','.safetensors','.pt','.pth','.onnx','.bin','.ckpt'}
SKIP={'node_modules','__pycache__','.git','.pytest_cache'}
TEXT={'.json','.jsonl','.md','.txt','.csv','.py','.js','.ts','.tsx','.html','.css','.yaml','.yml','.log','.svg','.patch','.toml','.mjs'}
def access(path):return Path('\\\\?\\'+str(path.resolve())) if os.name=='nt' else path
def content(path):return access(path).read_bytes()
def sha(data):return hashlib.sha256(data).hexdigest()
def clean(text):
    for value in [str(ROOT),str(ROOT).replace('\\','\\\\'),ROOT.as_posix()]:text=text.replace(value,'.')
    text=re.sub(r'C:(?:\\\\|\\|/)Users(?:\\\\|\\|/)Pasindu[^\r\n"<>]*', '[local path]',text,flags=re.I)
    return re.sub(r'assistant','assistant',text,flags=re.I)
def files(base):
    if not access(base).is_dir():return
    for parent,dirs,names in os.walk(access(base)):
        dirs[:]=[d for d in dirs if d not in SKIP and not d.startswith('.')]
        for name in names:
            if name in SKIP:continue
            p=Path(parent)/name
            if p.suffix.lower() not in WEIGHTS and not p.is_symlink() and p.is_file():
                yield Path(str(p).removeprefix('\\\\?\\'))
def dump(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(clean(json.dumps(value,ensure_ascii=False,indent=2)),encoding='utf-8')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    dest=Path(args.output).resolve();dest.mkdir(parents=True,exist_ok=True)
    assert dest!=ROOT and not ROOT.is_relative_to(dest),'Export into a separate publication directory.'
    web=dest/'docs';web.mkdir(exist_ok=True);manifest=[]
    def copy_tree(source,target,web_prefix=None):
        published=[]
        for p in files(source):
            relative=p.relative_to(source);target_file=target/relative;target_file.parent.mkdir(parents=True,exist_ok=True)
            original=content(p);data=clean(original.decode('utf-8',errors='replace')).encode('utf-8') if p.suffix.lower() in TEXT else original
            if p.suffix.lower()=='.html':data=data.replace(b'"/assets/',b'"./assets/').replace(b"'/assets/",b"'./assets/")
            target_file.write_bytes(data)
            record={'source':p.relative_to(ROOT).as_posix(),'published':target_file.relative_to(dest).as_posix(),'source_sha256':sha(original),'published_sha256':sha(data),'transformed':original!=data,'bytes':len(data)};manifest.append(record)
            if web_prefix is not None:
                url='./'+target_file.relative_to(web).as_posix();item={'name':relative.as_posix(),'url':url,'bytes':len(data)}
                if p.suffix.lower()=='.md':
                    preview=target_file.with_name(target_file.name+'.html');body=MarkdownIt('commonmark',{'html':False}).enable('table').render(data.decode())
                    preview.write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font:18px/1.65 system-ui;max-width:1100px;margin:auto;padding:28px;color:#1d1d1f}img{max-width:100%}pre,table{display:block;overflow:auto}code{overflow-wrap:anywhere}</style>'+body,encoding='utf-8');item['preview_url']='./'+preview.relative_to(web).as_posix()
                published.append(item)
        return published
    data=summary();reviews=judging();by_id={r['run_id']:r for r in reviews['rows']}
    baselines={r['run_id']:r for r in read_json(ROOT/'results/improvement_campaign/baseline_inventory.json',[])}
    campaigns={n:{e['run_id']:e for e in read_json(ROOT/folder/'campaign.json',{})['entries']} for n,folder in [(2,'results/improvement_campaign'),(3,'results/improvement_campaign/pass_2')]}
    initial=[];updated=[];results=[]
    def lightweight(row):
        keys=['run_id','model','task','sensory_track','case','start','end','status','error','pilot','repetition','task_seconds','protocol_hash','residency','config','performance','output_review','run_path']
        r={k:row.get(k) for k in keys};s=row['scores'];r['scores']={k:s.get(k) for k in ['verified_points','pending_points','quality_score','complete','rubric','categories','limitations']};r['scores']['evidence']={};return r
    for row in data['runs']:
        if row['run_id'] not in by_id:continue
        rid=row['run_id'];review=by_id[rid];base=baselines[rid];r=lightweight(row);initial.append(r)
        slug=rid.split('--')[-1];target=web/'results'/slug;attempts=[]
        for a in review['attempts']:
            n=a['number'];entry=campaigns[n][rid] if n>1 else None
            artifact=(Path(entry['further_folder']).parent/'evaluations'/entry['evaluation_id']/'artifacts') if entry else ROOT/base['run_path']/'artifacts'
            published=copy_tree(artifact,target/f'attempt-{n}',True)
            original_scores=entry['evaluation'].get('scores') if entry else base['scores']
            dump(target/f'attempt-{n}'/'automatic_scores.json',original_scores)
            prompt=(entry.get('review') or {}).get('prompt','') if entry else (ROOT/'benchmark/prompts'/f"{row['task']}_prompt.md").read_text(encoding='utf-8-sig')
            (target/f'attempt-{n}'/'prompt.md').write_text(clean(prompt),encoding='utf-8')
            game=target/f'attempt-{n}'/'game/dist/index.html'
            attempts.append({'number':n,'judgment':a,'files':published,'game_url':'./'+game.relative_to(web).as_posix() if game.exists() else None,'readiness':readiness(row['task'],original_scores),'prompt_url':'./'+(target/f'attempt-{n}'/'prompt.md').relative_to(web).as_posix()})
        working=Path(campaigns[3][rid]['further_folder']).parent;repair_entries=[]
        for repair in working.glob('repairs/*/repair.json'):
            info=read_json(repair,{});repair_target=target/'repairs'/repair.parent.name
            repair_files=copy_tree(repair.parent/'artifacts',repair_target,True);dump(repair_target/'repair.json',info)
            game=repair_target/'game/dist/index.html'
            repair_entries.append({'name':'GPT-6.1 Sol · separate small repair','lines':info['source_changed_lines'],'files':repair_files,'game_url':'./'+game.relative_to(web).as_posix() if game.exists() else None,'limitations':info.get('limitations',[])})
        results.append({'run_id':rid,'model':row['model']['name'],'task':row['task'],'case':row.get('case'),'track':row.get('sensory_track',''),'attempts':attempts,'repairs':repair_entries})
        revision=next((m for m in data['modifications'] if m['base_run_id']==rid and m.get('workspace_mode')),None)
        related=[m for m in data['modifications'] if m['base_run_id']==rid];extra=sum(m.get('extra_seconds',m.get('generation_seconds',0)) for m in related)
        updated.append({**r,'performance':(revision or {}).get('performance') or {**r['performance'],'generation_tps':None,'prompt_tps':None},'task_seconds':r['task_seconds']+extra,'after_updates':{'status':'evaluated','scored':True,'initial_seconds':r['task_seconds'],'extra_seconds':extra}})
        dump(target/'result.json',results[-1])
        (target/'README.md').write_text(f"# {row['model']['name']} · {row['task']} {row.get('case') or ''}\n\n[Main project README](../../../README.md) · [Interactive dashboard](https://maninka123.github.io/local-ai-benchmark/)\n\nOne final score: {review['final']['score']:.1f}/100 on attempt {review['final']['number']}. {'Fully complete.' if review['final']['completed'] else 'Incomplete after the third attempt.'}\n\n`attempt-1` is the initial result; `attempt-2` and `attempt-3` preserve the two follow-ups. Earlier failed attempts are unscored. Any `repairs` folder is separate and excluded from the model score.\n",encoding='utf-8')
    references=[]
    for task,title,brief in [('racing_game','3D racing game','A complete playable reference circuit racer.'),('data_analysis','Data analysis','One consolidated interactive analysis report.'),('detective','Detective investigation','All three cases in one reference investigation report.')]:
        source=ROOT/'results/references/gpt-6-astra-high'/task;target=web/'references'/task
        ref_files=copy_tree(source,target,True)
        references.append({'task':task,'title':title,'summary':brief,'url':'./'+(target/'output/index.html').relative_to(web).as_posix(),'prompt':(source/'prompt.md').read_text(encoding='utf-8-sig'),'files':ref_files})
    public_summary={**data,'runs':initial,'environment':{'cpu':'Intel Core i9-13900K','gpu':'NVIDIA RTX 4080','vram_gb':16,'ram_gb':64,'os':'Windows'},'running':None,'setup':None,'modifications':[{k:m.get(k) for k in ['base_run_id','generation_seconds','extra_seconds']} for m in data['modifications']]}
    dump(web/'data/snapshot.json',{'summary':public_summary,'updated':updated,'results':results,'references':references,'policy':reviews['policy']['description'],'published':now()})
    dump(web/'data/judgments.json',reviews)
    copy_tree(ROOT/'datasets',dest/'datasets');copy_tree(ROOT/'datasets',web/'inputs')
    for folder in ['benchmark','extensions','sandbox','scripts','tests','dashboard/backend','dashboard/frontend/src','dashboard/frontend/tests']:
        copy_tree(ROOT/folder,dest/folder)
    for name in ['config.yaml','requirements.txt','requirements.lock.txt','pyproject.toml','package.json','.env.example','dashboard/frontend/package.json','dashboard/frontend/package-lock.json','dashboard/frontend/index.html','dashboard/frontend/public.html','dashboard/frontend/vite.config.ts','dashboard/frontend/vite.public.config.ts','dashboard/frontend/tsconfig.json','dashboard/frontend/playwright.config.ts']:
        src=ROOT/name;p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(clean(src.read_text(encoding='utf-8')),encoding='utf-8')
    copy_tree(ROOT/'evaluation_private/scoring_config',dest/'evaluation_private/scoring_config')
    archives=[];archive_base=web/'downloads';archive_base.mkdir(exist_ok=True)
    # Full histories remain downloadable, including setup attempts and earlier evaluations.
    model_groups={}
    for model_dir in (ROOT/'models').iterdir():
        if model_dir.is_dir() and '--' in model_dir.name:model_groups.setdefault(model_dir.name.split('--')[0],[]).append(model_dir)
    for slug,model_dirs in model_groups.items():
        paths=[p for model_dir in model_dirs for p in files(model_dir)];further=ROOT/'results/further-work'/slug
        if further.exists():paths+=list(files(further))
        archive=archive_base/(slug+'.zip')
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in paths:
                raw=content(p);payload=clean(raw.decode('utf-8',errors='replace')).encode() if p.suffix.lower() in TEXT else raw
                z.writestr(p.relative_to(ROOT).as_posix(),payload)
        assert archive.stat().st_size<95_000_000,'Split this archive before GitHub upload.'
        archives.append({'model':slug,'url':'./downloads/'+archive.name,'bytes':archive.stat().st_size,'files':len(paths),'sha256':sha(archive.read_bytes())})
    dump(web/'data/archives.json',archives)
    snapshot=json.loads((web/'data/snapshot.json').read_text(encoding='utf-8'));snapshot['archives']=archives;dump(web/'data/snapshot.json',snapshot)
    dump(web/'data/manifest.json',{'generated':now(),'weight_files_included':0,'model_results':53,'attempts':159,'normalization':'Machine-local paths and assistant tooling names removed from publication copies; source outputs unchanged. HTML build asset paths made relative. Markdown preview companions added. Source/public hashes are recorded.','files':manifest})
    for path in [web/'results',web/'references',web/'inputs',web/'downloads',web/'data']:
        path.mkdir(exist_ok=True);(path/'README.md').write_text(f"# {path.name.replace('-',' ').title()}\n\n[Main README](../../README.md) · [Browse the interactive dashboard](https://maninka123.github.io/local-ai-benchmark/)\n\nSaved results and supporting evidence; no model weights. See the main README and methodology for interpretation.\n",encoding='utf-8')
    (web/'.nojekyll').write_text('',encoding='utf-8')
    (dest/'.gitignore').write_text('__pycache__/\n.pytest_cache/\n.venv/\nnode_modules/\n.env\nlogs/\nmodels/\nresults/\n*.gguf\n*.safetensors\n*.pt\n*.pth\n*.onnx\n*.bin\n*.ckpt\ndashboard/frontend/dist/\ndashboard/frontend/public-dist/\n*.tsbuildinfo\n',encoding='utf-8')
    print(json.dumps({'destination':str(dest),'model_results':len(results),'attempts':sum(len(r['attempts']) for r in results),'published_files':len(manifest),'archive_mb':round(sum(a['bytes'] for a in archives)/1e6,1)},indent=2))

if __name__=='__main__':main()
