"""Rebuild README figures from projected public measurements and output judgments."""
import json
from pathlib import Path
from collections import defaultdict
from statistics import mean
from urllib.request import urlopen
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/assets'
SOURCE = ROOT / 'docs/publication/chart-data.json'
TASKS = ['data_analysis', 'racing_game', 'detective']
NAMES = {'data_analysis': 'Data analysis', 'racing_game': 'Racing game', 'detective': 'Detective'}
COLORS = {'data_analysis': '#2563eb', 'racing_game': '#7c3aed', 'detective': '#d97706'}
LABELS = {
 'gemma4:12b-it-q4_K_M':'Gemma 4 12B', 'gemma4:26b-a4b-it-q4_K_M':'Gemma 4 26B',
 'glm-4.7-flash:q4_K_M':'GLM 4.7 Flash', 'laguna-xs.2:q4_K_M':'Laguna XS.2',
 'nemotron-3-nano:30b-a3b-q4_K_M':'Nemotron 3 Nano 30B', 'nemotron3:33b-q4_K_M':'Nemotron 3 Omni 33B',
 'qwen3.5:27b-q4_K_M':'Qwen 3.5 27B', 'qwen3.5:9b-q4_K_M':'Qwen 3.5 9B',
 'qwen3.6:35b-a3b-q4_K_M':'Qwen 3.6 35B', 'gpt-oss:20b':'GPT-OSS 20B',
 'qwen3-coder-next:q4_K_M':'Qwen 3 Coder Next', 'qwen3-next:80b-a3b-thinking-q4_K_M':'Qwen 3 Next 80B',
 'qwen3-vl:30b-a3b-instruct':'Qwen 3 VL 30B'}
plt.rcParams.update({'font.family':'Segoe UI', 'font.size':12, 'axes.titlesize':17,
 'axes.labelsize':12, 'figure.facecolor':'#fff', 'axes.facecolor':'#fff', 'text.color':'#172033',
 'axes.labelcolor':'#475569', 'xtick.color':'#475569', 'ytick.color':'#172033',
 'svg.fonttype':'path', 'axes.spines.top':False, 'axes.spines.right':False,
 'axes.spines.left':False, 'axes.spines.bottom':False})

def finite(x):
    return isinstance(x,(int,float)) and np.isfinite(x) and x >= 0
def average(xs):
    values = [x for x in xs if finite(x)]
    return mean(values) if values else None

def project():
    # Only deliberately selected scalars reach the publication data file.
    d = json.load(urlopen('http://127.0.0.1:8765/api/summary'))
    judgments = json.loads((ROOT/'results/judged_scores/reviewed_results.json').read_text(encoding='utf-8'))
    runs = {r['run_id']:r for r in d['runs']}
    models = {m['name']:m for m in d['models']}
    extras = defaultdict(float)
    for r in d['modifications']:
        extras[r['base_run_id']] += r.get('extra_seconds',r.get('generation_seconds',0)) or 0
    rows=[]
    for review in judgments['rows']:
        r=runs[review['run_id']]; m=models[review['model']]; p=m['parameter_comparison']['calculated']
        rows.append({'run_id':r['run_id'], 'model':review['model'], 'task':r['task'], 'case':r['case'],
          'track':r.get('sensory_track'), 'generation_tps':r['performance'].get('generation_tps'),
          'prompt_tps':r['performance'].get('prompt_tps'), 'initial_minutes':r['task_seconds']/60,
          'total_minutes':(r['task_seconds']+extras[r['run_id']])/60,
          'size_gb':m['size']/1e9, 'total_b':p['total']/1e9 if finite(p.get('total')) else None,
          'active_b':p['active']/1e9 if finite(p.get('active')) else None,
          'active_basis':'Installed GGUF tensor-shape structural estimate; not runtime activation tracing',
          'attempts':[{k:a.get(k) for k in ('number','completed')} for a in review['attempts']],
          'final_raw_quality':review['attempts'][-1]['raw_score'],
          'first_completed_attempt':review['first_completed_attempt'],
          'final_score':{1:100,2:60,3:30}.get(review['first_completed_attempt'], review['attempts'][-1]['raw_score']*.3)})
    payload={'source':'results/judged_scores/reviewed_results.json + projected /api/summary measurements',
     'scoring_policy':{'description':'Exactly one final score per result. Completed first: 100; second: 60; third: 30. Incomplete after third: final raw rubric quality × 0.3. Earlier failed attempts have status and notes, no awarded score.',
       'exclusions':'Time, throughput, hardware, frontier references and assisted repairs excluded.'},
     'aggregation':'Equal-weight case means within model/task/track. Missing measurements omitted.',
     'hardware':{'cpu':d['environment']['cpu'],'ram_bytes':d['environment']['ram_bytes'],
                 'gpu':'NVIDIA GeForce RTX 4080','vram_gib':16, 'logical_cores':d['environment']['logical_cores'],
                 'os':d['environment']['os']}, 'rows':rows}
    SOURCE.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return payload

def aggregate(rows):
    grouped=defaultdict(list)
    for r in rows:grouped[(r['model'],r['task'],r['track'])].append(r)
    points=[]
    for (model,task,track),group in grouped.items():
        p={'model':model,'task':task,'track':track,'cases':len(group)}
        for key in ('generation_tps','prompt_tps','initial_minutes','total_minutes','size_gb','total_b','active_b','final_score'):
            p[key]=average([r[key] for r in group])
        points.append(p)
    return points

def finish(fig, ax, filename, title, note):
    ax.set_title(title,loc='left',fontweight='bold',pad=22)
    ax.grid(axis='x',color='#e2e8f0',linewidth=.7);ax.set_axisbelow(True)
    # Interpretation belongs in the surrounding README, rather than tiny chart footnotes.
    fig.subplots_adjust(left=.36,right=.94,top=.88,bottom=.12)
    fig.savefig(OUT/filename,format='svg',metadata={'Creator':'Pasindu / local-ai-benchmark'})
    fig.savefig(OUT/filename.replace('.svg','.png'),dpi=200)
    plt.close(fig)

def plot_all(payload):
    points=aggregate(payload['rows']); order=sorted(LABELS, key=lambda m:LABELS[m])
    lookup={(p['model'],p['task']):p for p in points}
    for task in TASKS:
        data=sorted([p for p in points if p['task']==task],key=lambda p:p['final_score'] or 0)
        y=np.arange(len(data));fig,ax=plt.subplots(figsize=(8.3,6.8))
        b=np.array([p['final_score'] for p in data])
        ax.barh(y,b,height=.5,color=COLORS[task],alpha=.88)
        for i,v in enumerate(b):ax.text(v+1.1,i,f'{v:.1f}',va='center',fontsize=12)
        labels=[LABELS[p['model']]+(' [W]' if task=='detective' and p['track']=='text_only_detective' else ' [V]' if task=='detective' else '') for p in data]
        ax.set_yticks(y,labels);ax.set_xlim(0,35);ax.set_xlabel('Final completion-aware score / 100')
        note='One final score per task result. Unfinished after prompt 3: final rubric quality × 0.3. Time/repairs excluded.'
        if task=='detective':note='[V] visual evidence; [W] written evidence. Cases averaged equally. Tracks differ; not a common ranking.'
        finish(fig,ax,f'quality-{task}.svg',NAMES[task]+' · final score',note)

    # A stable task palette is reused in all multi-task figures.
    for key,filename,title,xlabel,note in [
      ('final_score','review-scores.svg','Final task scores','Final completion-aware score / 100','Exactly one score per result; complete prompt 1/2/3 = 100/60/30. Incomplete = 0–30. Detective V/W differ.'),
      ('generation_tps','token-speed.svg','Recorded initial generation speed','Output tokens / second','Initial inference only; weighted across calls within each run. Equal-weight Detective case means; unavailable omitted.'),
      ('total_minutes','total-time.svg','Time invested, including saved updates','Minutes per task result / Detective case','Initial + saved updates + re-evaluations; queue waiting excluded. Time has no effect on output-quality scores.')]:
        fig,ax=plt.subplots(figsize=(8.3,7.3));y=np.arange(len(order))
        for i,task in enumerate(TASKS):
            vs=[lookup.get((m,task),{}).get(key) for m in order]
            ys=[y[n]+(i-1)*.23 for n,v in enumerate(vs) if finite(v)]
            values=[v for v in vs if finite(v)]
            ax.barh(ys,values,height=.2,color=COLORS[task],label=NAMES[task],alpha=.88)
        ax.set_yticks(y,[LABELS[m]+(' [W]' if lookup.get((m,'detective'),{}).get('track')=='text_only_detective' else ' [V]') for m in order]);ax.invert_yaxis()
        ax.set_xlabel(xlabel);ax.legend(loc='lower right',frameon=False,fontsize=11)
        if key=='final_score':ax.set_xlim(0,35)
        finish(fig,ax,filename,title,note)

    unique={p['model']:p for p in points}
    for keys,filename,title,xlabel,note in [
      (['size_gb'],'model-storage.svg','Downloaded package size','Installed storage · decimal GB','Quantization differs across packages. File storage is not measured RAM or VRAM usage.'),
      (['total_b','active_b'],'model-parameters.svg','Total vs calculated active parameters','Billion parameters','Active counts are GGUF structural estimates, not measured expert routing. All weights still need to be available.')]:
        data=sorted(unique.values(),key=lambda p:p[keys[0]] or 0);y=np.arange(len(data));fig,ax=plt.subplots(figsize=(8.3,6.8))
        for i,key in enumerate(keys):
            vals=[p[key] for p in data];offset=(i-.5)*.3 if len(keys)>1 else 0
            available=[n for n,v in enumerate(vals) if finite(v)]
            ax.barh(y[available]+offset,[vals[n] for n in available],height=.28 if len(keys)>1 else .5,color='#2563eb' if i==0 else '#14b8a6',label='Total' if key=='total_b' else 'Calculated active' if key=='active_b' else 'Installed package')
            for n,v in enumerate(vals):
                if finite(v):ax.text(v+max([x for x in vals if finite(x)] or [1])*.025,n+offset,f'{v:.1f}',fontsize=12,va='center')
                else:ax.text(0,n+offset,'Unavailable',fontsize=11,va='center',color='#64748b')
        ax.set_yticks(y,[LABELS[p['model']] for p in data]);ax.set_xlabel(xlabel);ax.margins(x=.18)
        if len(keys)>1:ax.legend(frameon=False,loc='lower right',fontsize=11)
        finish(fig,ax,filename,title,note)

    # One final score per task; earlier failed prompts have no awarded score.
    matrix=np.array([[lookup[(m,task)]['final_score'] for task in TASKS] for m in order])
    fig,ax=plt.subplots(figsize=(8.3,6.8));ax.imshow(matrix,cmap='Blues',vmin=0,vmax=100,aspect='auto')
    ax.set_yticks(range(len(order)),[LABELS[m]+(' [W]' if lookup.get((m,'detective'),{}).get('track')=='text_only_detective' else ' [V]') for m in order]);ax.set_xticks(range(3),['Data','Racing','Detective']);ax.tick_params(length=0)
    for i in range(len(order)):
        for j in range(3):ax.text(j,i,f'{matrix[i,j]:.1f}',ha='center',va='center',color='white' if matrix[i,j]>60 else '#172033')
    finish(fig,ax,'quality-progress.svg','Final score by task','One final awarded score per result; Detective case means. Visual/written evidence differs; earlier failures have no score.')

    fig,ax=plt.subplots(figsize=(8.3,6.8))
    for i,m in enumerate(order):
        p=unique[m];q=average([x['final_score'] for x in points if x['model']==m]);ax.scatter(p['size_gb'],q,s=85,color='#2563eb',marker='o',edgecolor='white',lw=1)
        ax.annotate(f'M{i+1}',(p['size_gb'],q),xytext=(5,5),textcoords='offset points',fontsize=12)
    ax.set_xlabel('Installed package size · GB');ax.set_ylabel('Mean final task score / 100');ax.set_ylim(0,35)
    # Two columns of readable model keys avoid a miniature footnote-style legend.
    for i,m in enumerate(order):
        column=i//7;row=i%7
        track=' [W]' if lookup.get((m,'detective'),{}).get('track')=='text_only_detective' else ' [V]'
        fig.text(.10+column*.46,.205-row*.024,f'M{i+1}  {LABELS[m]}{track}',fontsize=11,color='#475569')
    ax.set_title('Capacity vs final task score',loc='left',fontweight='bold',pad=22);ax.grid(color='#e2e8f0');ax.set_axisbelow(True)
    fig.subplots_adjust(left=.13,right=.94,top=.88,bottom=.32)
    fig.savefig(OUT/'quality-vs-storage.svg',metadata={'Creator':'Pasindu / local-ai-benchmark'})
    fig.savefig(OUT/'quality-vs-storage.png',dpi=200);plt.close(fig)
    report={'figures':sorted(p.name for p in OUT.glob('*.svg')), 'reviewed_results':len(payload['rows']),
      'models':len(unique),'complete_results':sum(r['first_completed_attempt'] is not None for r in payload['rows']),
      'final_scores_finite':bool(np.isfinite(matrix).all()),'all_figures_nonempty':all(p.stat().st_size>1000 for p in OUT.glob('*.svg')),
      'font':'Segoe UI; SVG glyphs converted to paths to preserve the installed font on GitHub',
      'png_export_dpi':200,
      'notes':['No model weights, personal environment paths, process lists or private expected answers exported.',
               'AI rubric judgments are distinct from human ratings and preserved automatic scores.',
               'No throughput or time contribution to rubric scores; repaired outputs excluded.']}
    (ROOT/'docs/publication/figure-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    payload=json.loads(SOURCE.read_text(encoding='utf-8')) if SOURCE.exists() else project()
    plot_all(payload)
