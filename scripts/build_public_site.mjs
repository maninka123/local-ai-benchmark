import {cp,mkdir,rename} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const built=path.join(root,'dashboard/frontend/public-dist'),docs=path.join(root,'docs');
await mkdir(docs,{recursive:true});
await cp(built,docs,{recursive:true});
await rename(path.join(docs,'public.html'),path.join(docs,'index.html'));
console.log('Built GitHub Pages dashboard in docs/. Saved data and outputs preserved.');
