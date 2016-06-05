import re
class Key:
  def __init__(self, lower=False, array=False, search=False, remove=None, join=None):
    self.search = search
    self.array = array
    self.remove = remove
    self.join = join
    self.lower= lower

  def parse(self, value):
    if self.lower:
      value = value.lower()

    if self.remove :
      value = re.sub(re.compile(self.remove), "", value)

    if self.join:
      words = re.split(self.join, value)
      value = words[0]
      for word in words[1:]:
        value += word[0].upper() + word[1:]
    return value
