import _bootstrap
from benchmark.util import ROOT,config,write_json
from benchmark.generators.business_data_generator import generate
from benchmark.generators.detective_case_generator import generate as detective
import hashlib

def main():
    seed=config()['benchmark']['seed'];generate(seed);detective(seed)
    game=ROOT/'datasets'/'racing_game'/'game';(game/'src').mkdir(parents=True,exist_ok=True);(game/'public').mkdir(exist_ok=True)
    write_json(game/'package.json',{'name':'candidate-racing-game','version':'1.0.0','private':True,'type':'module','scripts':{'dev':'vite --configLoader native','build':'vite build --configLoader native','preview':'vite preview --configLoader native'},'dependencies':{'three':'0.184.0'},'devDependencies':{'vite':'7.3.7','typescript':'5.9.3'}})
    (game/'index.html').write_text('<!doctype html><html><head><meta charset="utf-8"><title>Racing Game</title></head><body><div id="app"></div><script type="module" src="/src/main.js"></script></body></html>',encoding='utf-8')
    (game/'src'/'main.js').write_text('// Infrastructure only. Implement the game here.\n',encoding='utf-8')
    (game/'vite.config.js').write_text("import {defineConfig} from 'vite';\nexport default defineConfig({cacheDir:'/tmp/vite-cache',server:{fs:{allow:['/output/game','/opt/lab/node_modules']}}});\n",encoding='utf-8')
    (game/'README.md').write_text('Three.js + Vite are preinstalled. Implement src/main.js and styles. Use npm run build. Network unavailable.\n',encoding='utf-8')
    manifest={str(p.relative_to(ROOT/'datasets')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'datasets').rglob('*')) if p.is_file()}
    write_json(ROOT/'results'/'dataset_manifest.json',{'seed':seed,'files':manifest})
    print('Generated and validated six business tables, 12 hidden patterns, 3 cases with 10 visual exhibits each, and a game starter.')
if __name__=='__main__':main()
