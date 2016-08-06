import re
from .Interpreted import Interpreted
from ..utils import joinStr, ucfirst
class Interpreter:

  def __init__(self, syntax, handlers, modules_folder=None, extensions=[], extra_extensions=[], keys=[], defaultHandler=None):
    self.syntax = syntax
    self.handlers = handlers
    self.keys = keys
    self.extensions = extensions
    self.extra_extensions = extra_extensions
    self.defaultHandler = defaultHandler
    self.defaultHandlerName = defaultHandler.name if defaultHandler else None
    self.modules_folder = modules_folder

  def onCreateStatements(self, handler, sSelection, statements=None):
    obj = {}

    if not statements:
      statements = handler.getStatements(sSelection)

    for key in statements:
      fn = getattr(self, joinStr("parse" + ucfirst(key) + "Key"),  None)
      if callable(fn):
        obj[key] = fn(statements[key])
      else:
        obj[key] = statements[key]
    return obj

  def interprete(self, sSelection):
    matched = None
    for handler in self.handlers:
      match = handler.match(sSelection)
      if match and handler.force:
        return Interpreted(self, handler, sSelection,match)
      elif match and (not matched or handler.name == self.defaultHandlerName):
        matched = Interpreted(self, handler, sSelection,match)

    if not matched:
      return Interpreted(self, self.getDefaultHandler(), sSelection, None)

    return matched

  def getDefaultHandler(self):
    return self.defaultHandler if self.defaultHandler else self.handlers[0]

  def setDefaultHandler(self, handlerName):
    for handler in self.handlers:
      if handler.name == handlerName:
        self.defaultHandler = handler
        self.defaultHandlerName = handler.name
        return

  def setStatementsByOption(self, interpreted, option_obj):
    interpreted.statements['module'] = option_obj['value']
