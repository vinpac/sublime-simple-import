import re
from .Interpreted import Interpreted
from ..SImport import SImport
from ..utils import joinStr, ucfirst
class Interpreter:

  @staticmethod
  def createMatchers(arr, matchers):
    result = []
    for matcher in arr:
      _m = matcher
      for key in matchers:
        _m = _m.replace("{"+ key +"}", "(?P<"+ key +">"+ matchers[key] +")")
      result.append(re.compile(_m))
    return result

  def __init__(self, syntax, handlers, keys=[], defaultHandler=None):
    self.syntax = syntax
    self.handlers = handlers
    self.keys = keys
    self.defaultHandler = defaultHandler
    self.defaultHandlerName = defaultHandler.name if defaultHandler else None

  def parseStatements(self, statements):
    for key in statements:
      fn = getattr(self, joinStr("parse" + ucfirst(key) + "Key"),  None)
      if callable(fn):
        statements[key] = fn(statements[key])
    return statements

  def interprete(self, sSelection):
    matched = None
    for handler in self.handlers:
      match = handler.match(sSelection)
      if match and handler.force:
        return Interpreted(self, handler, match)
      elif match and (not matched or handler.name == self.defaultHandlerName):
        matched = Interpreted(self, handler, match)

    if not matched:
      return Interpreted(self, self.getDefaultHandler(), None)

    return matched

  def getDefaultHandler(self):
    print(self.defaultHandler)
    return self.defaultHandler if self.defaultHandler else self.handlers[0]

  def setDefaultHandler(self, handlerName):
    for handler in self.handlers:
      if handler.name == handlerName:
        self.defaultHandler = handler
        self.defaultHandlerName = handler.name
        return

  def resolve(self, sSelection):
    return SImport(self.interprete(sSelection), sSelection)
