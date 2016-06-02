from ..utils import expressionInContext
import re

class Handler:

    def __init__(self, name, matchers, result):
      self.name = name
      self.matchers = matchers
      self.result = result

      arr = re.findall(r"\{\w+\}", self.result)
      self.keys = [ x[1:-1] for x in arr]

    def match(self, expression, context):
      for matcher in self.matchers:
        match = matcher.match(context)
        if match:
          return match

    def getStatements(self, expression, context, match=None):
      if not match:
        match = self.match(expression, context)

      if match:
        statements = match.groupdict()
        values = list(statements.values())
      else:
        statements = {}
        values = expressionInContext(expression, context).split(":")

      keys = self.keys
      index = 0
      length = len(values)

      for key in keys:
        if not key in statements:
          statements[key] = values[index]
          index = min(index + 1, length - 1)

      print(statements)
      return statements

    def getResultWithStatements(self, statements):
      result = self.result
      for key in statements:
        result = result.replace("{"+key+"}", statements[key])
      return result
