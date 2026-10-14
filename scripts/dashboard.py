import _bootstrap
import uvicorn
from benchmark.util import config
if __name__=='__main__':
    cfg=config()['dashboard'];uvicorn.run('dashboard.backend.app:app',host=cfg['host'],port=cfg['port'])
