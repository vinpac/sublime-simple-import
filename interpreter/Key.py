class Key:
  def __init__(self, array=False, search=False, remove=None, join=None):
    self.search = search
    self.array = array
    self.remove = remove
    self.join = join

  def parse(self, value):
    if self.remove :
      value = re.sub(re.compile(self.remove), "", value)

    if self.join:
      value = value 

    return value
