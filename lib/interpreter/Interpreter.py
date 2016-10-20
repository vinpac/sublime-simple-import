import re
from os import path
from ..utils import joinStr, ucfirst
from .Interpreted import Interpreted
from ..utils import endswith
from ..utils import extract_suffix
from ..SIMode import SIMode
from ..SimpleImport import SimpleImport

class Interpreter:

  @staticmethod
  def parseInterpreterName(name):
    if name.endswith("Interpreter"):
      return name[:-11].lower()
    else:
      return name.lower()

  def __init__(self):
    self.find_imports_regex = None
    self.find_exports_regex = None
    self.defaultHandler = None
    self.syntax = Interpreter.parseInterpreterName(type(self).__name__)
    self.handlers = []
    self.keys = {}
    self.settings = {}
    self.__settings = {}


    # Run callbacks
    self.run()
    self.afterRun()

  def isCompatibleView(self, filename, syntax):
    extensions = self.getSetting("extensions", [])
    if endswith(extensions, filename):
      return True
    else:
      return re.search(r"^\.?{0}".format(self.syntax), syntax, re.IGNORECASE)

  def run(self):
    return True

  def afterRun(self):
    self.__settings = self.settings.copy()

    if not self.syntax:
      SimpleImport.log_error("Missing syntax on {0}".format(type(self).__name__))

  def parseModuleKey(self, value):
    #remove extensions
    for ext in self.getSetting('remove_extensions'):
      if value.endswith(ext):
        value = value[0:-len(ext)]
        break
    return value

  def parseStatements(self, statements):
    for key in statements:
      fn = getattr(self, joinStr("parse" + ucfirst(key) + "Key"),  None)
      if callable(fn):
        statements[key] = fn(statements[key])

  def getSetting(self, key, otherwise=None):
    return self.__settings[key] if key in self.__settings else otherwise

  def onInterprete(self, interpreted, mode=SIMode.REPLACE_MODE):
    if not len(interpreted.statements.keys()):
      interpreted.statements['module'] = interpreted.simport.expression

    self.parseStatements(interpreted.statements)

  def getHandlerBySelection(self, sSelection):
    handler = None

    for n_handler in self.handlers:
      match = n_handler.match(sSelection)

      if match:
        handler = n_handler
        break

    if not handler:
      handler = self.getDefaultHandler()

    return handler

  def interprete(self, sSelection, mode=SIMode.REPLACE_MODE):
    handler = self.getHandlerBySelection(sSelection)
    if handler:
      interpreted = Interpreted(self, handler.getStatements(sSelection), handler.name, sSelection)
    else:
      interpreted = Interpreted(self, {}, None, sSelection)

    # fire onInterprete
    self.onInterprete(interpreted, mode)

    return interpreted

  def getDefaultHandler(self):
    if self.defaultHandler:
      return self.getHandlerByName(self.defaultHandler)
    elif self.handlers:
      return self.handlers[0]

  def onSearchResultChosen(self, interpreted, option_key, value, mode=SIMode.REPLACE_MODE):
    interpreted.statements['module'] = value
    self.parseStatements(interpreted.statements)

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

      extension = extract_suffix(extensions, filename)
      if not extension:
        return False

      normalizedValued = self.normalizeValue(path.join(dirpath, filename[:len(extension) * -1]))
      return re.search(regex, "{0}{1}".format(normalizedValued, extension), re.IGNORECASE)
    return re.search(regex, filename, re.IGNORECASE)

  def getHandlerByName(self, handlerName):
    for handler in self.handlers:
      if handler.name == handlerName:
        return handler

  def parseOptions(self, interpreted, options):
    return options

