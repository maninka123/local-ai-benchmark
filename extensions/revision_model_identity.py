"""Record linked Ollama package changes in separate further-work identities."""
import hashlib,json,os,re
from pathlib import Path
LIST='application/vnd.ollama.manifest.list.v2+json'
MANIFEST='application/vnd.docker.distribution.manifest.v2+json'
IMAGE='application/vnd.ollama.image.'

def check(name,original_digest,current_digest,store=None):
    if original_digest==current_digest:return {'kind':'same_digest'}
    store=Path(store or os.environ.get('OLLAMA_MODELS','D:/LocalLLM/models'))
    def blob(digest):
        digest=digest.removeprefix('sha256:')
        if not re.fullmatch('[0-9a-f]{64}',digest):raise ValueError('Invalid digest')
        path=store/'blobs'/('sha256-'+digest)
        if path.stat().st_size>2_000_000:raise ValueError('Not a manifest')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Invalid cached manifest hash')
        return json.loads(raw)
    def signature(manifest,weights=True):
        if manifest.get('schemaVersion')!=2 or manifest.get('mediaType')!=MANIFEST:raise ValueError('Unsupported manifest')
        if not any(l['mediaType']==IMAGE+'model' for l in manifest['layers']):raise ValueError('Missing model')
        kept=[]
        for layer in manifest['layers']:
            kind=layer['mediaType']
            if kind in [LIST,MANIFEST,IMAGE+'license']:continue
            if not kind.startswith(IMAGE):raise ValueError('Unknown model layer')
            if not weights and kind in [IMAGE+'model',IMAGE+'projector']:continue
            kept.append((kind,layer['digest'],layer['size']))
        return manifest['config'],sorted(kept)
    try:
        old=blob(original_digest);new=blob(current_digest)
        if signature(old)==signature(new):kind='manifest_metadata_update'
        else:
            repository,tag=name.rsplit(':',1);parts=repository.split('/')
            if len(parts)==1:parts.insert(0,'library')
            if any(not re.fullmatch('[a-zA-Z0-9._-]+',p) for p in [*parts,tag]):return None
            envelope=json.loads((store/'manifests'/'registry.ollama.ai'/Path(*parts)/tag).read_text())
            variants=[v for layer in envelope.get('layers',[]) if layer['mediaType']==LIST for v in blob(layer['digest'])['manifests']]
            if not any(v['digest']=='sha256:'+current_digest for v in variants):return None
            if not any(signature(blob(v['digest']))==signature(old) for v in variants):return None
            if signature(old,False)[1]!=signature(new,False)[1]:return None
            old_config=blob(old['config']['digest']);new_config=blob(new['config']['digest'])
            keys=['model_format','model_family','model_type','file_type','renderer','parser']
            if any(old_config.get(k)!=new_config.get(k) for k in keys):return None
            if not old_config.get('model_family') or not old_config.get('model_format'):return None
            kind='linked_runtime_variant'
        return {'kind':kind,'original_digest':original_digest,'current_digest':current_digest,'runner':new.get('runner'),'format':new.get('format'),
                'note':'This package identity applies only to further work. Initial benchmark identity is preserved. Linked runtime variants are not claimed to have byte-identical weights or identical performance.'}
    except (OSError,ValueError,KeyError,TypeError):return None
