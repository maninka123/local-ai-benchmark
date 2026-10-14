import {existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
// Normal npm install uses the local dependency. The supplied evaluation sandbox is a read-only fallback.
const local = new URL('./node_modules/three/build/three.module.js', import.meta.url);
const provided = new URL('../../../../../../sandbox/node_modules/three/build/three.module.js', import.meta.url);
export default {base:'./', resolve:{alias:{three:fileURLToPath(existsSync(local)?local:provided)}}, server:{host:'127.0.0.1'}, build:{chunkSizeWarningLimit:650}};
