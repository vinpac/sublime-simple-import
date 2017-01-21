import re
from os import path
from ..interpreter import *
from ..SIMode import SIMode
from ..utils import endswith

class ScssInterpreter(Interpreter):
  def run(self):
    self.settings = {
      "extensions": [".scss"],
      "remove_extensions": [".scss"],
      "extra_extensions": [".jpg", ".png", ".gif", ".svg"],
      "ignore": [ "node_modules", ".git" ]
    }

  def parseModuleKey(self, value):
    if "/" in value:
      if value.startswith("./"):
        value = value[2:]

      if path.basename(value).startswith("_"):
        value = path.join(path.dirname(value), path.basename(value)[1:])

    return super().parseModuleKey(value)

  def onSearchResultChosen(self, interpreted, option_key, value, mode=SIMode.REPLACE_MODE):
    if option_key == "extra_files":
      interpreted.handler_name = "file"

    super().onSearchResultChosen(interpreted, option_key, value, mode)

  def stringifyStatements(self, statements, handler_name=None, insert_type=Interpreted.IT_REPLACE):
    if handler_name == "file":
      return "url({0})".format(statements["module"])

    if self.getSetting("single-quotes"):
      return "@import \'{0}\';".format(statements["module"])

    return "@import \"{0}\";".format(statements["module"])

  def getQueryObject(self, interpreted):
    return {
      "file": interpreted.statements["module"]
    }
