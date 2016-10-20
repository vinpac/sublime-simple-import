import re

class Handler:
  @staticmethod
  def joinStatements(s1, s2):
    for key in s2:
      if not key in s1:
        s1[key] = s2[key]
        pass

      if type(s1[key]) is list:
        s1[key] = s1[key] + list(set(s2[key]) - set(s1[key]))
      else:
        s1[key] = s2[key]

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
