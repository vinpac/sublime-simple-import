import re
from os import path
from ..interpreter import *
from ..SIMode import SIMode

class ScssInterpreter(Interpreter):
  def run(self):
    self.settings = {
      "extensions": [".scss"],
      "remove_extensions": [".scss"],
      "extra_extensions": [ ".jpg", ".png", ".gif", ".svg" ],
      "excluded_paths": [ "node_modules", ".git" ]
    }

  def parseModuleKey(self, value):
    if "/" in value:
      if value.startswith("./"):
        value = value[2:]

      if path.basename(value).startswith("_"):
        value = path.join(path.dirname(value), path.basename(value)[1:])

    return super().parseModuleKey(value)

  def stringifyStatements(self, statements, itype=None, insert_type=Interpreted.IT_REPLACE):
    return "@import \"{0}\";".format(statements["module"])

  def getQueryObject(self, interpreted):
    return {
      "file": interpreted.statements["module"]
    }
