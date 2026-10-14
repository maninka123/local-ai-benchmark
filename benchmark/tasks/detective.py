from inspect_ai import task
from benchmark.harness.runner import make_task
@task
def detective(**kwargs):return make_task('detective',**kwargs)
