def browser_probe(box):
    return box.exec(['node','/opt/lab/browser_probe.mjs'],timeout=120,category='browser_testing')
