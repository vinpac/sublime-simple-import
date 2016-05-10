from ..interpreter import *

class JavascriptInterpreter(Interpreter):
  def __init__(self):
    self.syntax = "javascript"

    self.handlers = [
      Handler(
        name="import",
        matchers=[
          Matcher("import {variable}"),
          Matcher("import {variable} from {module}")
        ],
        result="import {variable} from \"{module}\""
      ),
      Handler(
        name="import_from",
        matchers=[
          Matcher("{submodule}::{module}"),
          Matcher("extends {module}\\.{submodule}")
        ],
        result="import { {submodule} } from \"{module}\""
      ),
      Handler(
        name="require",
        matchers=[
          Matcher("require {variable}"),
          Matcher("(const|let|var) {variable}"),
          Matcher("(const|let|var) {variable} = {module}")
        ],
        result="const {variable} = require(\"{module}\")"
      )
    ]

    self.keys = {
      "submodules": Key(
        array=True
      ),
      "module": Key(
        search=True
      ),
      "variable": Key(
        remove=r"!|@|\*",
        join=r"\/|-|\."
      )
    }
