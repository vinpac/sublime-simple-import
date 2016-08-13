import sublime, re
from os import path
from ..utils import joinStr
from ..interpreter import *


class JavascriptInterpreter(Interpreter):

  def __init__(self):

    self.find_imports_regex = r"(import[\s\n]+((?:(?!from)[\s\S])*)[\s\n]+from[\s]+[\"\']([^\"\']+)[\"\'])"
    self.find_exports_regex = r"(export\s+(const|let|var|function|class)\s+(?P<value>[\w]+))"

    keys = {
      "variable": "[^\s]+",
      "module": "[^\s]+",
      "submodule": "[^\s]+",
      "submodules": "((?:(?!from)[\s\S])*)"
    }

    self.syntax = "javascript"
    self.settings = {
      "extensions": [".js", ".jsx"],
      "remove_extensions": [".js", ".jsx"],
      "extra_extensions": [".jpg", ".svg", ".json", ".gif", ".css", ".scss", ".less"],
      "excluded_paths": ["node_modules", ".git"],
      "modules_folder": "node_modules"
    }

    self.handlers = [
      Handler(
        name="import_all_from",
        matchers=[
          "import \* as {variable} from {module}",
          "{variable}\.\*"
        ],
        keys=keys,
        force=True
      ),
      Handler(
        name="import_pure",
        matchers=[
          "imp {module}"
        ],
        keys=keys
      ),
      Handler(
        name="import_from",
        matchers=[
          "import {{submodules}} from [\'\"]{module}[\'\"]",
          "import {variable}, {{submodules}} from [\'\"]{module}[\'\"]",
          "{submodule}::{module}"
        ],
        keys=keys
      ),
      Handler(
        name="import",
        matchers=[
          "import {variable} from [\'\"]{module}[\'\"]",
          "{variable}\.[^\s]+",
          "import {variable}",
          "(?P<module>[^\s\.]+)(\.[^\s]+){2,}"
        ],
        keys=keys
      ),
      Handler(
        name="require_from",
        matchers=[
          "require {module}\.{submodule}",
          "{submodule}::{module}",
          "{module}\.{submodule}"
        ],
        keys=keys
      ),
      Handler(
        name="require",
        matchers=[
          "require {variable}",
          "(const|let|var) {variable}",
          "(const|let|var) {variable} = {module}"
        ],
        keys=keys
      ),
      Handler(
        name="require_plain",
        matchers=[
          "req {variable}"
        ],
        keys=keys
      )
    ]

    self.setDefaultHandler("import")

  def removeExtensions(self, value):
    extensions = self.getSetting('extensions', []) + self.getSetting('extra_extensions', [])
    for ext in extensions:
      if value.endswith(ext):
        return value[0:-len(ext)]
    return value


  def parseModuleKey(self, value):
    #remove extensions
    for ext in self.getSetting('remove_extensions'):
      if value.endswith(ext):
        value = value[0:-len(ext)]
        break

    # remove /index from path
    if "/" in value and value.endswith("/index"):
      value = value[:-6]

    return value

  def parseSubmodulesKey(self, value):
    if type(value) is list :
      return value

    submodules = value.split(',')
    return [ submodule.strip() for submodule in submodules ]

  def parseVariableKey(self, value):
    return joinStr(re.sub(r"!|@|\*", "", value), r"\/|-|\.")

  def getQueryObject(self, interpreted):
    return interpreted.statements["module"]

  def onSearchResultChosen(self, interpreted, option_key, value, PANEL_MODE=False):
    statements = interpreted.statements
    if (PANEL_MODE and len(statements['variable'])) or option_key == "containing_files":
      interpreted.itype = "import_from"
      statements['submodules'] = self.parseSubmodulesKey(interpreted.statements['variable'])
      del statements['variable']
    elif PANEL_MODE:
      if option_key != "modules":
        statements['variable'] = path.basename(value)
      statements['variable'] = self.parseVariableKey(self.removeExtensions(statements['variable']))

    statements['module'] = self.parseModuleKey(value)

  def onInterprete(self, interpreted):
    statements = interpreted.statements
    if len(statements.keys()) == 0:
      values = interpreted.simport.expression.split(":")
      length = len(values)

      if length > 2:
        statements["module"] = values[-1]
        statements["submodules"] = values[:-1]
      else:
        statements["variable"] = values[0]
        statements["module"] = values[1] if length == 2 else statements["variable"]

    if "module" not in statements:
      statements["module"] = statements["variable"]

    if "submodule" in statements:
      if "submodules" not in statements:
        statements["submodules"] = []
      statements["submodules"].append(statements["submodule"])
      statements.pop("submodule")

    return super().onInterprete(interpreted)

  def stringifyStatements(self, statements, itype=None, insert_type=Interpreted.IT_REPLACE):
    import_str = ''

    if itype.startswith('require'):
      if 'variable' in statements:
        import_str = 'const '
        import_str += statements['variable']
        import_str += ' = '

      if 'module':
        import_str += "require('{0}')".format(statements['module'])

    else:
      import_str = 'import '
      if itype != "import_pure":
        if itype == "import_all_from":
          import_str += "* as "

        if 'variable' in statements:
          import_str += statements['variable']

        if 'submodules' in statements:
          if 'variable' in statements:
            import_str += ', '
          import_str += "{{ {0} }}".format(", ".join(statements['submodules']))

        import_str += " from "

      import_str += "\'{0}\'".format(statements['module'])

    if insert_type == Interpreted.IT_INSERT_AFTER:
      import_str = "\n" + import_str
    elif insert_type == Interpreted.IT_INSERT:
      import_str += "\n"

    return import_str

  def parseBeforeInsert(self, interpreted, view_imports, NO_REPLACE_MODE=False, PANEL_MODE=False):
    if interpreted.itype.startswith('import'):
      regex = r"^{0}({1})?$".format(
        interpreted.statements['module'],
        "|".join(self.getSetting('remove_extensions'))
      )

      for vimport in view_imports:
        if re.search(regex, vimport.statements['module']):
          Interpreter.joinStatements(vimport.statements, interpreted.statements)
          vimport.insert_type = Interpreted.IT_REPLACE_IMPORT
          return vimport

    if NO_REPLACE_MODE or PANEL_MODE:
      if len(view_imports):
        region_point = view_imports[-1].simport.context_region.end()
        interpreted.insert_type = Interpreted.IT_INSERT_AFTER
        interpreted.simport.context_region = sublime.Region(region_point, region_point)
      else:
        interpreted.insert_type = Interpreted.IT_INSERT

    return interpreted
