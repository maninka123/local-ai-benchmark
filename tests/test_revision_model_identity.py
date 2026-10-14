import hashlib,json
from extensions.revision_model_identity import check,IMAGE,MANIFEST,LIST

def fixture(tmp_path,split=False,changed_params=False,linked=True):
    blobs=tmp_path/'blobs';blobs.mkdir()
    def save(value):
        raw=json.dumps(value).encode();digest=hashlib.sha256(raw).hexdigest();(blobs/('sha256-'+digest)).write_bytes(raw);return digest
    metadata={'model_format':'gguf','model_family':'example','model_type':'30B','file_type':'Q4_K_M','renderer':'example','parser':'example'}
    config=save({**metadata,'rootfs':{}});newconfig=save(metadata)
    def layer(kind,digest):return {'mediaType':IMAGE+kind,'digest':'sha256:'+digest,'size':10}
    base={'schemaVersion':2,'mediaType':MANIFEST,'config':{'digest':'sha256:'+config},'layers':[layer('model','1'*64),layer('params','2'*64)]}
    old=save(base);new={**base,'runner':'ggml','format':'gguf'}
    if split:new={**new,'runner':'llamacpp','config':{'digest':'sha256:'+newconfig},'layers':[layer('model','3'*64),layer('projector','4'*64),layer('params','5'*64 if changed_params else '2'*64)]}
    current=save(new)
    variants=save({'schemaVersion':2,'mediaType':LIST,'manifests':[{'digest':'sha256:'+old},{'digest':'sha256:'+current}]})
    tag=tmp_path/'manifests/registry.ollama.ai/library/example/latest';tag.parent.mkdir(parents=True)
    tag.write_text(json.dumps({**base,'layers':base['layers']+([{'mediaType':LIST,'digest':'sha256:'+variants}] if linked else [])}))
    return old,current

def test_metadata_change_retains_weights_and_settings(tmp_path):
    old,current=fixture(tmp_path)
    assert check('example:latest',old,current,tmp_path)['kind']=='manifest_metadata_update'

def test_explicit_runtime_variant_records_distinct_identity(tmp_path):
    old,current=fixture(tmp_path,split=True)
    result=check('example:latest',old,current,tmp_path)
    assert result['kind']=='linked_runtime_variant' and result['current_digest']==current
    assert 'not claimed' in result['note']

def test_changed_prompt_settings_are_rejected(tmp_path):
    old,current=fixture(tmp_path,split=True,changed_params=True)
    assert check('example:latest',old,current,tmp_path) is None

def test_unlinked_weight_change_is_rejected(tmp_path):
    old,current=fixture(tmp_path,split=True,linked=False)
    assert check('example:latest',old,current,tmp_path) is None

def test_corrupt_cached_manifest_is_rejected(tmp_path):
    old,current=fixture(tmp_path)
    (tmp_path/'blobs'/('sha256-'+current)).write_text('{}')
    assert check('example:latest',old,current,tmp_path) is None
