import re
from os import path
from ..utils import joinStr, ucfirst
from .Interpreted import Interpreted
from ..utils import endswith
from ..utils import getsuffix
from ..SIMode import SIMode

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

  def __init__(self, syntax, handlers, settings={}, keys=[], defaultHandler=None):
    self.syntax = syntax
    self.handlers = handlers
    self.keys = keys
    self.defaultHandler = defaultHandler
    self.default_settings = settings
    self.settings = self.default_settings.copy()
    self.find_imports_regex = None
    self.find_exports_regex = None

  def getSetting(self, key, otherwise=None):
    return self.settings[key] if key in self.settings else otherwise

  def onInterprete(self, interpreted, mode=SIMode.REPLACE_MODE):
    for key in interpreted.statements:
      fn = getattr(self, joinStr("parse" + ucfirst(key) + "Key"),  None)
      if callable(fn):
        interpreted.statements[key] = fn(interpreted.statements[key])

  def interprete(self, sSelection, mode=SIMode.REPLACE_MODE):
    matched_handler = None

    for handler in self.handlers:
      match = handler.match(sSelection)
      if match:
        matched_handler = handler
        break

    if not matched_handler:
      matched_handler = self.getDefaultHandler()

    statements = handler.getStatements(sSelection)

    interpreted = Interpreted(self, matched_handler.getStatements(sSelection), matched_handler.name, sSelection)
    self.onInterprete(interpreted, mode=mode)
    return interpreted

  def getDefaultHandler(self):
    return self.defaultHandler if self.defaultHandler else self.handlers[0]

  def onSearchResultChosen(self, interpreted, option_key, value, mode=SIMode.REPLACE_MODE):
    if mode == SIMode.PANEL_MODE:
      interpreted.statements['variable'] = path.basename(value)
    interpreted.statements['module'] = value

  def parseBeforeInsert(self, interpreted, view_imports, mode=SIMode.REPLACE_MODE):
    return interpreted

  def getFileMatcher(self, value):
    return r"({0}|{1})(\/index)?({2})$".format(
      value,
      self.normalizeValue(value),
      "|".join(self.getSetting('extensions', [])))

  def getExtraFilesMatcher(self, value):
    return r"({0}|{1})({2})$".format(
      value,
      self.normalizeValue(value),
      '|'.join(self.getSetting('extra_extensions', []))
    )

  def isValidFile(self, filename):
    return endswith(self.getSetting('extensions', []), filename)

  def isValidExtraFile(self, filename):
    return endswith(self.getSetting('extra_extensions', []), filename)

  def normalizeValue(self, value):
    return re.sub(r"-|\.", "", value).lower()

  def matchFilePathWithRegex(self, filename, regex, dirpath=None, is_extra=False):
    if dirpath:
      extensions = self.getSetting('extensions' if not is_extra else 'extra_extensions', [])

      extension = getsuffix(extensions, filename)
      if not extension:
        return False

      normalizedValued = self.normalizeValue(path.join(dirpath, filename[:len(extension) * -1]))
      return re.search(regex, "{0}{1}".format(normalizedValued, extension), re.IGNORECASE)
    return re.search(regex, filename, re.IGNORECASE)

  def setDefaultHandler(self, handlerName):
    for handler in self.handlers:
      if handler.name == handlerName:
        self.defaultHandler = handler
        self.defaultHandlerName = handler.name
        return

