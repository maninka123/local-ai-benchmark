def execute(box, command):
    return box.exec(['bash','-lc',command])
