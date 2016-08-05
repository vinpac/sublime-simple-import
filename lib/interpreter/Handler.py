import re

class Handler:

  def __init__(self, name, matchers, result, force=False):
    self.name = name
    self.matchers = matchers
    self.result = result
    self.force = force

    arr = re.findall(r"\{\w+\}", self.result)
    self.keys = [ x[1:-1] for x in arr]

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

    keys = self.keys
    index = 0
    length = len(values)

    for key in keys:
      if not key in statements:
        statements[key] = values[index]
        index = min(index + 1, length - 1)

    return statements

  def getResultWithStatements(self, statements):
    result = self.result
    for key in statements:
      result = result.replace("{"+key+"}", statements[key])
    return result
