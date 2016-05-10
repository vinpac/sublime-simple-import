from ..interpreter import *
from ..SimpleImport import SImport
class Interpreter:

  def __init__(self, syntax, handlers, keys=[]):
    self.syntax = syntax
    self.createHandlers(handlers)
    self.createKeys(keys)

  def createKeys(self, keys):
    self.keys = {}
    for name in keys:
      self.keys[name] = Key(name, keys[name])

  def parseStatements(self, statements):
    for key in statements:
      if key in self.keys:
        statements[key] = self.keys[key].parse(statements[key])
    return statements

  def createHandlers(self, handlers):
    self.handlers = []
    for key in handlers:
      obj = handlers[key]
      try:
        handler = Handler(obj["match"], obj["result"])
      except KeyError:
        print("Error creating Handler from dict")

      self.handlers.append( handler )

      if( "default" in handlers[key] and handlers[key]["default"] == True):
        self.defaultHandler = self.handlers[-1]

    if not self.defaultHandler and len(handlers):
      self.defaultHandler = self.handlers[1]

  def interprete(self, expression, context):
    for handler in self.handlers:
      match = handler.match(expression, context)
      if match:
        return Interpreted(self, handler, match)

    return Interpreted(self, handler)

  def resolve(self, sSelection):
    return SImport(self.interprete(sSelection.expression, sSelection.context), sSelection)
