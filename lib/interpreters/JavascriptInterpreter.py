import re
from ..interpreter import *
from ..utils import joinStr

class JavascriptInterpreter(Interpreter):
  def __init__(self):
    keys = {
      "variable": "[^\s]+",
      "module": "[^\s]+",
      "submodule": "[^\s]+"
    }

    self.syntax = "javascript"
    self.extensions = ["js", "jsx"]
    self.modules_folder = 'node_modules'

    self.exports = [
      "export (const|let|var|function|class) {value}",
      "export {\s*{values}\s*}",
      "exports\.{value} ="
    ]

    self.handlers = [
      Handler(
        name="import_all_from",
        matchers=Interpreter.createMatchers([
          "import {variable}\.\*",
          "{variable}\.\*"
        ], keys),
        result="import * as {variable} from \'{module}\'",
        force=True
      ),
      Handler(
        name="import_from_prefixed",
        matchers=Interpreter.createMatchers([
          "import {submodule}\.{module}"
        ], keys),
        result="import { {submodule} } from \'{module}\'",
        force=True
      ),
      Handler(
        name="require_from",
        matchers=Interpreter.createMatchers([
          "require {module}\.{submodule}",
          "{submodule}::{module}",
          "extends {module}\.{submodule}"
        ], keys),
        result="const {submodule} = require(\'{module}\').{submodule}"
      ),
      Handler(
        name="import_from",
        matchers=Interpreter.createMatchers([
          "{submodule}::{module}",
          "{module}\.{submodule}",
          "extends {module}\.{submodule}"
        ], keys),
        result="import { {submodule} } from \'{module}\'"
      ),
      Handler(
        name="import",
        matchers=Interpreter.createMatchers([
          "import {variable}",
          "(?P<module>[^\s\.]+)(\.[^\s]+){2,}",
          "import {variable} from {module}"
        ], keys),
        result="import {variable} from \'{module}\'"
      ),
      Handler(
        name="require",
        matchers=Interpreter.createMatchers([
          "require {variable}",
          "(const|let|var) {variable}",
          "(const|let|var) {variable} = {module}"
        ], keys),
        result="const {variable} = require(\'{module}\')"
      ),
      Handler(
        name="require_plain",
        matchers=Interpreter.createMatchers([
          "req {variable}"
        ], keys),
        result="require(\'{module}\')"
      )
    ]

    self.setDefaultHandler("import")

  def parseSubmodules(self, value):
    values = value.split(",")
    v = []

    for name in values:
      v.append( self.parseVariableName(name.strip()) )

    return v.join(', ')

  def parseSubmoduleKey(self, value):
    return self.parseVariableKey(value)

  def parseModuleKey(self, value):
    return value.lower()

  def parseVariableKey(self, value):
    return joinStr(re.sub(r"!|@|\*", "", value), r"\/|-|\.")
