class PendingImport:

  key_str = {
    "files": "Import",
    "modules": "Import Module",
    "containing_files": "Import From",
    "extra_files": "Import"
  }

  def __init__(self, interpreted, options):
    self.interpreted = interpreted
    self.options = options
    self.resolved = False

  def getOptionsArr(self, include_keys=False):
    arr = []
    for key in self.options:
      if include_keys:
        arr += [ "{key}: {value}".format(key=PendingImport.key_str[key], value=option) for option in self.options[key] ]
      else:
        arr += self.options[key]
    return arr

  def getOptionByIndex(self, index):
    i = 0
    for key in self.options:
      length = len(self.options[key])
      if index < length:
        return { "key": key, "value": self.options[key][index]  }
      index = index - length
