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

  def getStatements(self, sSelection, match=None):
    if not match:
      match = self.match(sSelection)

    if match:
      statements = match.groupdict()
      values = list(statements.values())
    else:
      statements = {}
      values = sSelection.expression_in_context.split(":")
      values_len = len(values)
      index = 0

    return statements
