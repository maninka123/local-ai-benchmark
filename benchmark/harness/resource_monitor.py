import threading,time,csv,psutil,os
from benchmark.util import now

class ResourceMonitor:
    def __init__(self,run):
        self.run=run;self.stop_event=threading.Event();self.rows=[];self.nvml=None;self.error=None
        try:
            import pynvml
            pynvml.nvmlInit();self.nvml=pynvml;self.gpu=pynvml.nvmlDeviceGetHandleByIndex(0)
        except Exception as e:self.error=str(e)
    def sample(self):
        p=psutil.Process(os.getpid());mem=psutil.virtual_memory()
        row={'timestamp':now(),'monotonic_seconds':time.perf_counter(),'cpu_percent':psutil.cpu_percent(),
            'ram_used_bytes':mem.used,'ram_percent':mem.percent,'controller_rss_bytes':p.memory_info().rss,
            'inference_process_rss_bytes':None,'gpu_utilization_percent':None,'gpu_memory_bytes':None,'gpu_temperature_c':None,'gpu_power_w':None}
        total=0
        for proc in psutil.process_iter(['name','memory_info']):
            if (proc.info['name'] or '').lower() in ['ollama.exe','llama-server.exe']:total+=proc.info['memory_info'].rss if proc.info['memory_info'] else 0
        row['inference_process_rss_bytes']=total
        if self.nvml:
            try:
                n=self.nvml;row.update(gpu_utilization_percent=n.nvmlDeviceGetUtilizationRates(self.gpu).gpu,
                    gpu_memory_bytes=n.nvmlDeviceGetMemoryInfo(self.gpu).used,gpu_temperature_c=n.nvmlDeviceGetTemperature(self.gpu,n.NVML_TEMPERATURE_GPU),gpu_power_w=n.nvmlDeviceGetPowerUsage(self.gpu)/1000)
            except Exception as e:self.error=str(e)
        self.rows.append(row)
        with (self.run/'hardware_metrics.csv').open('a',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(row));
            if len(self.rows)==1:writer.writeheader()
            writer.writerow(row)
    def loop(self):
        while not self.stop_event.is_set():
            try:self.sample()
            except Exception as e:self.error=str(e)
            self.stop_event.wait(1)
    def start(self):
        self.thread=threading.Thread(target=self.loop,daemon=True);self.thread.start();return self
    def stop(self):self.stop_event.set();self.thread.join(5)
    def summary(self):
        def peak(key):return max((r[key] for r in self.rows if r[key] is not None),default=None)
        energy=sum((b['monotonic_seconds']-a['monotonic_seconds'])*(a['gpu_power_w']+b['gpu_power_w'])/2 for a,b in zip(self.rows,self.rows[1:]) if a['gpu_power_w'] is not None and b['gpu_power_w'] is not None)
        return {'samples':len(self.rows),'peak_vram_bytes':peak('gpu_memory_bytes'),'peak_ram_bytes':peak('ram_used_bytes'),
            'peak_inference_rss_bytes':peak('inference_process_rss_bytes'),'peak_gpu_temperature_c':peak('gpu_temperature_c'),
            'estimated_gpu_energy_joules':energy if any(r['gpu_power_w'] is not None for r in self.rows) else None,
            'energy_method':'Trapezoidal integral of whole-device NVML power samples at ~1 Hz; includes background GPU activity. Estimated, not whole-PC energy.',
            'nvml_error':self.error}
