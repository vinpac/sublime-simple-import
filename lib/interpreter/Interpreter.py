import re
from ..utils import joinStr, ucfirst
from .Interpreted import Interpreted

class Interpreter:

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

  def __init__(self, syntax, handlers, settings={}, extensions=[], extra_extensions=[], keys=[], defaultHandler=None):
    self.syntax = syntax
    self.handlers = handlers
    self.keys = keys
    self.extensions = extensions
    self.extra_extensions = extra_extensions
    self.defaultHandler = defaultHandler
    self.settings = settings
    self.find_imports_regex = None
    self.find_exports_regex = None

  def getSetting(self, key):
    return self.settings[key] if key in self.settings else None

  def onInterprete(self, interpreted):
    for key in interpreted.statements:
      fn = getattr(self, joinStr("parse" + ucfirst(key) + "Key"),  None)
      if callable(fn):
        interpreted.statements[key] = fn(interpreted.statements[key])

  def interprete(self, sSelection):
    matched_handler = None

    for handler in self.handlers:
      match = handler.match(sSelection)
      if match:
        matched_handler = handler
        break

    if not matched_handler:
      matched_handler = self.getDefaultHandler()

    statements = handler.getStatements(sSelection)

    return Interpreted(self, matched_handler.getStatements(sSelection), matched_handler.name, sSelection)

  def getDefaultHandler(self):
    return self.defaultHandler if self.defaultHandler else self.handlers[0]

  def onSearchResultChosen(self, interpreted, option_key, value):
    interpreted.statements['module'] = value

  def resolveSimilarImports(self, interpreted, view_imports):
    return interpreted

  def getFileQueryRegex(self, filename):
    return r"({0}|{0}\/index)({1})$".format(filename, "|".join(self.getSetting('extensions')))

  def getExtraFileQueryRegex(self, filename):
    return r"{0}({1})".format(filename, "|".join(self.getSetting('extra_extensions')))


  def setDefaultHandler(self, handlerName):
    for handler in self.handlers:
      if handler.name == handlerName:
        self.defaultHandler = handler
        self.defaultHandlerName = handler.name
        return
