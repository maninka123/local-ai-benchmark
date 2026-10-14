from inspect_ai import task
from benchmark.harness.runner import make_task
@task
def data_analysis(**kwargs):return make_task('data_analysis',**kwargs)
