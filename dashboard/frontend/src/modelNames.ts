// Display labels only. Keep exact package IDs as select values, storage keys and API identities.
const labels:Record<string,string>={
 'gemma4:12b-it-q4_K_M':'Gemma 4 · 12B',
 'gemma4:26b-a4b-it-q4_K_M':'Gemma 4 · 26B',
 'glm-4.7-flash:q4_K_M':'GLM 4.7 Flash',
 'laguna-xs.2:q4_K_M':'Laguna XS.2',
 'nemotron-3-nano:30b-a3b-q4_K_M':'Nemotron 3 Nano · 30B',
 'nemotron3:33b-q4_K_M':'Nemotron 3 · 33B',
 'qwen3.5:27b-q4_K_M':'Qwen 3.5 · 27B',
 'qwen3.5:9b-q4_K_M':'Qwen 3.5 · 9B',
 'qwen3.6:35b-a3b-q4_K_M':'Qwen 3.6 · 35B',
 'gpt-oss:20b':'GPT-OSS · 20B',
 'qwen3-coder-next:q4_K_M':'Qwen 3 Coder Next',
 'qwen3-next:80b-a3b-thinking-q4_K_M':'Qwen 3 Next · 80B',
 'qwen3-vl:30b-a3b-instruct':'Qwen 3 VL · 30B',
 'gpt-6-astra-high':'GPT-6 Astra · High',
};

export function modelLabel(name:string):string{
 // An unknown package keeps its complete ID so variants can never silently merge.
 return labels[name]??name;
}
