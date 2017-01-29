import re
from sublime import Region
from os import path, walk
from ..utils import joinStr, ucfirst
from .Interpreted import Interpreted
from ..utils import endswith
from ..utils import extract_suffix
from ..SIMode import SIMode

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
      print("Simple Import Error -> {0}".format(message))

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

  def setSettings(self, settings):
    self.__settings = settings

  def onInterprete(self, interpreted, mode=SIMode.REPLACE_MODE):
    if not len(interpreted.statements.keys()):
      interpreted.statements['module'] = interpreted.simport.expression

    self.parseStatements(interpreted.statements)

  def getHandlerBySelection(self, simport):
    handler = None
    for n_handler in self.handlers:
      match = n_handler.match(simport)
      if match:
        simport.region = Region(simport.context_region.end() - len(match.group(0)), simport.context_region.end())
        return n_handler

    return self.getDefaultHandler()

  def interprete(self, simport, mode=SIMode.REPLACE_MODE):
    handler = self.getHandlerBySelection(simport)
    if handler:
      interpreted = Interpreted(self, handler.getStatements(simport), handler.name, simport)
    else:
      interpreted = Interpreted(self, {}, None, simport)

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

  def buildRegexForFiles(self, value):
    return r"({0}|{1})(\/index)?({2})$".format(
      value,
      self.normalizeValue(value),
      "|".join(self.getSetting('extensions', [])))

  def buildRegexForExtraFiles(self, value):
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

      normalizedValued = self.normalizeValue(
        path.join(dirpath, filename[:len(extension) * -1])
      )
      return re.search(regex, "{0}{1}".format(normalizedValued, extension), re.IGNORECASE)
    return re.search(regex, filename, re.IGNORECASE)

  def getHandlerByName(self, handlerName):
    for handler in self.handlers:
      if handler.name == handlerName:
        return handler

  def getQueryValue(self, interpreted):
    return False

  def findAllModules(self, project_path):
    return []

  def findByValue(self, value, project_path, omit_files=None):
    result = {}
    regex_for_files = self.buildRegexForFiles(value)
    regex_for_extra_files = self.buildRegexForExtraFiles(value)
    ignored_paths = [
      path.normpath(epath)
      for epath in self.getSetting("ignore", [])
    ]


    for dirpath, dirnames, filenames in walk(project_path, topdown=True):
      relative_dir = path.relpath(dirpath, project_path)
      # Change excluding folders
      dirnames[:] = [dirname for dirname in dirnames if path.normpath(path.join(relative_dir, dirname)) not in ignored_paths]
      for filename in filenames:
        if omit_files and path.join(relative_dir, filename) in omit_files:
          continue

        # Find files with name equal the value
        if self.matchFilePathWithRegex(
          filename, regex_for_files, dirpath=relative_dir
        ):
          if "files" not in result:
            result["files"] = []

          result["files"].append(path.join(relative_dir, filename))
        elif self.matchFilePathWithRegex(
          filename, regex_for_extra_files, dirpath=relative_dir, is_extra=True
        ):
          if "extra_files" not in result:
            result["extra_files"] = []

          result["extra_files"].append(path.join(relative_dir, filename))
          pass

    return result

  def parsePath(self, path):
    if path[:2] == "./" or path[:3] == "../":
      return path
    else:
      return "./" + path

  def parseOptions(self, interpreted, options):
    return options

  def parseOptionItem(self, option, view_relpath):
    if not option:
      return option

    # Make every path relative to view file
    if option["key"] not in ["modules", "module_exports", "module_files"]:
      option["value"] = self.parsePath(
        path.normpath(
          path.relpath(
            option["value"],
            view_relpath
          )
        )
      )
    return option

