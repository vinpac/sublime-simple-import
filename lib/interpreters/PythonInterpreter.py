import re
from os import path
from ..interpreter import *
from ..SimpleImport import SimpleImport

class PythonInterpreter(Interpreter):

  def __init__(self):
    self.find_imports_regex = None
    self.find_exports_regex = None

    keys = {
      "module": "[^\s]+",
      "variable": "[^\s]+"
    }

    self.syntax = "python"
    self.settings = {
      "extensions": [".py"],
      "remove_extensions": [".py"],
      "extra_extensions": [],
      "modules_folder": None
    }

    self.handlers = [
      Handler(
        name="import_all",
        matchers=[
          "from {variable} import \*",
          "{module}\.\*"
        ],
        keys=keys
      ),
      Handler(
        name="import_from",
        matchers=[
          "from {module} import {variable}",
          "{variable}\:\:{module}"
        ],
        keys=keys
      ),
      Handler(
        name="import",
        matchers=[
          "import {module}"
        ],
        keys=keys
      )
    ]

    self.setDefaultHandler("import")

  def parseModuleKey(self, value):
    for ext in self.getSetting('remove_extensions'):
      if value.endswith(ext):
        value = value[0:-len(ext)]
        break
    return value.replace("/", ".")[1:] if "/" in value else value

  def parseVariableKey(self, value):
    return re.sub(r"!|@|\*", "", value)

  def getQueryObject(self, interpreted):
    return {
      "file": interpreted.statements["module"]
    }

  def onInterprete(self, interpreted, mode=SimpleImport.REPLACE_MODE):
    statements = interpreted.statements

    if not len(statements.keys()):
      statements['module'] = interpreted.simport.expression
    else:
      if "variable" not in statements:
        statements["variable"] = statements["module"]

    return super().onInterprete(interpreted)

  def onSearchResultChosen(self, interpreted, option_key, value, mode=SimpleImport.REPLACE_MODE):
    if option_key != 'modules':
      value = path.dirname(value) if value.endswith('/__init__.py') else value

    interpreted.statements['module'] = self.parseModuleKey(value)

  def stringifyStatements(self, statements, itype=None, insert_type=Interpreted.IT_INSERT):
    if itype == "import":
      return "import {0}".format(statements['module'])

    return "from {0} import {1}".format(statements['module'], statements['variable'])

  def parseBeforeInsert(self, interpreted, view_imports, mode=SimpleImport.REPLACE_MODE):
    return interpreted

  def getFileQueryRegex(self, filename):
    return r"({0}|{0}\/__init__)({1})$".format(filename, "|".join(self.getSetting('extensions')))
