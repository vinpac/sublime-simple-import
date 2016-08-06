import re

class Handler:

  @staticmethod
  def createMatchers(matchers, keys):
    result = []
    for matcher in matchers:
      _m = matcher
      for key in keys:
        _m = _m.replace("{"+ key +"}", "(?P<"+ key +">"+ keys[key] +")")
      result.append(re.compile(_m))
    return result

  def __init__(self, name, matchers, keys, force=False):
    self.name = name
    self.matchers = self.createMatchers(matchers, keys)
    self.force = force

  def match(self, sSelection):
    for matcher in self.matchers:
      match = re.search(matcher, sSelection.context)
      if match:
        return match

  def getStatements(self, sSelection):
    match = self.match(sSelection)

    return match.groupdict() if match else {}
