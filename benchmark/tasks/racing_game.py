from inspect_ai import task
from benchmark.harness.runner import make_task
@task
def racing_game(**kwargs):return make_task('racing_game',**kwargs)
