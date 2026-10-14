import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],base:'/local-ai-benchmark/',build:{rollupOptions:{input:'public.html'},assetsDir:'app-assets',outDir:'public-dist',emptyOutDir:true}});
