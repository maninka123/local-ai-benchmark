import httpx, fnmatch, platform, subprocess, shutil, psutil, importlib.metadata
from benchmark.util import ROOT,config,write_json,now

def discover():
    cfg=config()['benchmark'];base=cfg['base_url'];models=[]
    with httpx.Client(timeout=60) as client:
        version=client.get(base+'/api/version').json()
        for item in client.get(base+'/api/tags').json()['models']:
            if any(fnmatch.fnmatch(item['name'].lower(),p.lower()) for p in cfg['excluded_models']):continue
            if cfg['selected_models'] and item['name'] not in cfg['selected_models']:continue
            show=client.post(base+'/api/show',json={'model':item['name']}).json()
            info=show.get('model_info',{});details=show.get('details',{});arch=info.get('general.architecture',details.get('family'))
            models.append({**item,'architecture':arch,'parameters':details.get('parameter_size'),
                'parameter_count':info.get('general.parameter_count'),'active_parameters':info.get('general.active_parameter_count'),
                'quantization':details.get('quantization_level'),'capabilities':show.get('capabilities',[]),
                'vision':'vision' in show.get('capabilities',[]),'tools':'tools' in show.get('capabilities',[]),
                'context_length':info.get(str(arch)+'.context_length'),'show':show})
    write_json(ROOT/'models'/'discovered.json',{'timestamp':now(),'ollama':version,'models':models})
    return sorted(models,key=lambda m:m['size'])

def environment():
    def cmd(args):
        try:return subprocess.run(args,capture_output=True,text=True,timeout=20).stdout.strip()
        except Exception as e:return 'unavailable: '+str(e)
    value={'timestamp':now(),'os':platform.platform(),'cpu':cmd(['powershell','-NoProfile','-Command','(Get-CimInstance Win32_Processor).Name']),
        'logical_cores':psutil.cpu_count(),'ram_bytes':psutil.virtual_memory().total,'python':platform.python_version(),
        'node':cmd(['node','--version']),'docker':cmd(['docker','version','--format','{{json .}}']),
        'nvidia':cmd(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader']),
        'cuda_advertised':cmd(['nvidia-smi']),
        'disks':{p:shutil.disk_usage(p)._asdict() for p in ['C:/','D:/']},
        'packages':{p:importlib.metadata.version(p) for p in ['inspect-ai','pandas','numpy','psutil','nvidia-ml-py','httpx']}}
    write_json(ROOT/'results'/'environment.json',value);return value
