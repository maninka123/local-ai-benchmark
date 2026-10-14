def execute_python(box, code):
    return box.exec(['python','-c',code],category='python_execution')
