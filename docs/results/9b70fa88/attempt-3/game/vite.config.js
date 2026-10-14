import {defineConfig} from 'vite';
export default defineConfig({cacheDir:'/tmp/vite-cache',server:{fs:{allow:['/output/game','/opt/lab/node_modules']}}});
