"""Display-only parameter estimates; never modify recorded benchmark metrics."""
import math,re,struct
from functools import lru_cache
from pathlib import Path

# Publisher model cards, checked 2026-10-10. Counts are rounded by publishers.
REPORTED={
 'qwen3-vl:30b':(30e9,3e9,'https://huggingface.co/Qwen/Qwen3-VL-30B-A3B-Instruct'),
 'gpt-oss:20b':(20.9e9,3.6e9,'https://huggingface.co/openai/gpt-oss-20b'),
 'qwen3-coder-next:':(80e9,3e9,'https://huggingface.co/Qwen/Qwen3-Coder-Next'),
 'qwen3-next:80b':(80e9,3e9,'https://huggingface.co/Qwen/Qwen3-Next-80B-A3B-Thinking'),
 'qwen3.5:9b':(9e9,None,'https://huggingface.co/Qwen/Qwen3.5-9B'),
 'qwen3.5:27b':(27e9,None,'https://huggingface.co/Qwen/Qwen3.5-27B'),
 'gemma4:12b':(11.95e9,None,'https://huggingface.co/google/gemma-4-26B-A4B-it'),
 'laguna-xs.2':(33e9,3e9,'https://huggingface.co/poolside/Laguna-XS.2'),
 'qwen3.6':(35e9,3e9,'https://huggingface.co/Qwen/Qwen3.6-35B-A3B'),
 'gemma4:26b':(25.2e9,3.8e9,'https://huggingface.co/google/gemma-4-26B-A4B-it'),
 'glm-4.7-flash':(30e9,3e9,'https://huggingface.co/zai-org/GLM-4.7-Flash'),
 'nemotron-3-nano:':(30e9,3.5e9,'https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16'),
 'nemotron3:33b':(30e9,3e9,'https://github.com/NVIDIA-NeMo/Nemotron/blob/main/docs/nemotron/omni3/architecture.md'),
}

def tensor_directory(path):
    """Read GGUF v2/v3 metadata and tensor shapes, without reading weight data."""
    with Path(path).open('rb') as f:
        def unpack(code):
            raw=f.read(struct.calcsize('<'+code))
            if len(raw)!=struct.calcsize('<'+code):raise ValueError('Truncated GGUF header')
            return struct.unpack('<'+code,raw)[0]
        def string():return f.read(unpack('Q')).decode('utf-8')
        sizes={0:1,1:1,2:2,3:2,4:4,5:4,6:4,7:1,10:8,11:8,12:8}
        def skip(kind,count=1):
            if kind in sizes:f.seek(sizes[kind]*count,1)
            elif kind==8:
                for _ in range(count):f.seek(unpack('Q'),1)
            elif kind==9:
                for _ in range(count):sub=unpack('I');length=unpack('Q');skip(sub,length)
            else:raise ValueError('Unknown GGUF value type')
        if f.read(4)!=b'GGUF' or unpack('I') not in (2,3):raise ValueError('Unsupported GGUF')
        tensors=unpack('Q');fields=unpack('Q')
        for _ in range(fields):string();skip(unpack('I'))
        result=[]
        for _ in range(tensors):
            name=string();dims=[unpack('Q') for _ in range(unpack('I'))];unpack('I');unpack('Q')
            result.append((name,dims))
        return result

@lru_cache(maxsize=32)
def calculated(digest,modelfile,architecture,expert_count,used_count,parameter_count):
    paths=[Path(line[5:].strip().strip('"')) for line in modelfile.splitlines() if line.startswith('FROM ')]
    try:
        parts=[tensor_directory(p) for p in paths if p.is_file()]
        if not parts:raise ValueError('Installed tensor directory unavailable')
        # Some Ollama packages embed the vision tower in the main GGUF.
        auxiliary=lambda name:name.startswith(('v.','vision.','audio.','mm.'))
        language=[(name,dims) for name,dims in parts[0] if not auxiliary(name)]
        total=sum(math.prod(dims) for _,dims in language)
        extras=sum(math.prod(dims) for part in parts[1:] for _,dims in part)+sum(math.prod(dims) for name,dims in parts[0] if auxiliary(name))
        if expert_count and used_count:
            routed=[(name,dims) for name,dims in language if re.search(r'\.ffn_(?:gate_up|gate|up|down)_exps\.',name)]
            if not routed or any(expert_count not in dims for _,dims in routed):raise ValueError('Routed expert shapes unavailable')
            routed_count=sum(math.prod(dims) for _,dims in routed)
            active=total-routed_count*(1-used_count/expert_count)
            method=f'Installed GGUF tensor count minus inactive routed expert weights ({used_count} of {expert_count} experts per MoE layer). Shared experts, attention, embeddings and other weights, including any prediction heads, retained. Auxiliary encoders excluded from the text calculation. Parameter-count conventions differ from publisher counts.'
        else:
            active=total;method='Dense model: all language-model weights counted as active by convention. Embedding lookups and modality-specific encoders make actual per-token usage different.'
        return {'total':total,'active':active,'percent':100*active/total,'auxiliary_parameters':extras,'method':method,'basis':'Installed tensor shapes; estimate, not observed expert activations'}
    except (OSError,ValueError,UnicodeError,struct.error) as e:
        return {'total':parameter_count,'active':None,'percent':None,'method':str(e),'basis':'Calculation unavailable'}

VIDEO_REFERENCES={
 'qwen3.5:':'https://huggingface.co/Qwen/Qwen3.5-9B',
 'qwen3.6:':'https://huggingface.co/Qwen/Qwen3.6-35B-A3B',
 'qwen3-vl:':'https://huggingface.co/Qwen/Qwen3-VL-30B-A3B-Instruct',
 'gemma4:':'https://huggingface.co/google/gemma-4-26B-A4B-it',
 'nemotron3:33b':'https://github.com/NVIDIA-NeMo/Nemotron/blob/main/docs/nemotron/omni3/README.md',
}

def enrich(model):
    info=model.get('show',{});metadata=info.get('model_info',{});arch=model.get('architecture','')
    report=next((v for k,v in REPORTED.items() if model['name'].startswith(k)),None)
    reported={'total':report[0],'active':report[1],'percent':100*report[1]/report[0] if report[1] else None,'source':report[2],'checked':'2026-10-10'} if report else {
        'total':model.get('parameter_count'),'active':model.get('active_parameters'),'percent':None,'source':None,'basis':'Installed model metadata; publisher active count not recorded'}
    calc=calculated(model['digest'],info.get('modelfile',''),arch,metadata.get(arch+'.expert_count'),metadata.get(arch+'.expert_used_count'),model.get('parameter_count'))
    video_source=next((v for k,v in VIDEO_REFERENCES.items() if model['name'].startswith(k)),None)
    video={'supported':bool(model.get('vision') and video_source),'note':'Video understanding (model capability). Video files need frame extraction in this Ollama setup; video has not been benchmarked.','source':video_source}
    return {**{k:v for k,v in model.items() if k!='show'},'input_video':video,'parameter_comparison':{'reported':reported,'calculated':calc,'runtime':{'active':None,'note':'Ollama did not record expert activation traces. Token speed and VRAM cannot determine an active parameter count.'}}}
