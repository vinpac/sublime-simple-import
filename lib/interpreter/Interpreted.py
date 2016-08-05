class Interpreted:
  key_str= {
    "files": "Import",
    "modules": "Import Module",
    "containing_files": "Import From",
    "extra_files": "Import"
    }

  def __init__(self, interpreter, handler, sSelection, match=None):
    self.interpreter = interpreter
    self.handler = handler
    self.match = match
    self.sSelection = sSelection

    self.statements = handler.getStatements(sSelection, match)
    self.options = {}

  def __str__(self):
    return self.handler.getResultWithStatements(interpreter.parseStatements(self.statements))

  def getOptionsArr(self):
    arr = []
    for key in self.options:
      arr = arr + [ "{key}: {value}".format(key=Interpreted.key_str[key], value=option) for option in self.options[key] ]
    return arr

  def getOptionObjectByIndex(self, index):
    i = 0
    for key in self.options:
      i += len(self.options[key])
      if index < i:
        return { "key": key, "value": self.options[key][index - (i - 1)]  }

  def setStatementsByOption(self, option_obj):
    print(self.statements)
