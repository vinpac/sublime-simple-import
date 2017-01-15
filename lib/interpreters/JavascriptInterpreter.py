import re
from sublime import Region
from os import path
from ..utils import joinStr
from ..interpreter import *
from ..SIMode import SIMode

class JavascriptInterpreter(Interpreter):

  def run(self):

    self.find_imports_regex = r"(import[\s\n]+((?:(?!from|;)[\s\S])*)[\s\n]+from[\s]+[\"\']([^\"\']+)[\"\'](;?))"
    self.find_exports_regex = r"(export\s+(const|let|var|function|class)\s+(?P<value>[\w]+))"

    keys = {
      "variable": "[^\s]+",
      "module": "[^\s]+",
      "submodule": "[^\s]+",
      "submodules": "((?:(?!from)[\s\S])*)"
    }

    self.settings = {
      "extensions": [".js", ".jsx"],
      "remove_extensions": [".js"],
      "extra_extensions": [".png", ".jpg", ".jpeg", ".svg", ".json", ".gif", ".css", ".scss", ".less"],
      "ignore": ["node_modules", ".git"],
      "modules_folder": "node_modules",
      "require_by_default": False,
      "add_semicolon": True
    }

    self.handlers = [
      Handler(
        name="import_all_from",
        matchers=[
          "import \* as {variable} from {module};?",
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
          "import {{submodules}} from [\'\"]{module}[\'\"];?",
          "import {variable}, {{submodules}} from [\'\"]{module}[\'\"];?",
          "{submodule}::{module}"
        ],
        keys=keys
      ),
      Handler(
        name="import",
        matchers=[
          "import {variable} from [\'\"]{module}[\'\"];?",
          "{variable}\.[^\s]+$",
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
          "{module}\.{submodule}$"
        ],
        keys=keys
      ),
      Handler(
        name="require_plain",
        matchers=[
          "req {variable}"
        ],
        keys=keys
      ),
      Handler(
        name="require",
        matchers=[
          "require {variable}",
          "(const|let|var) {variable} = {module}",
          "(const|let|var) {variable}"
        ],
        keys=keys
      )
    ]

    self.defaultHandler = "import"

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

  def onSearchResultChosen(self, interpreted, option_key, value, mode=SIMode.REPLACE_MODE):
    statements = interpreted.statements
    if (mode == SIMode.PANEL_MODE and len(statements['variable'])) or option_key == "containing_files":
      interpreted.handler_name = "import_from"
      statements['submodules'] = self.parseSubmodulesKey(interpreted.statements['variable'])
      del statements['variable']
    elif mode == SIMode.PANEL_MODE:
      if option_key != "modules":
        statements['variable'] = path.basename(value)
      statements['variable'] = self.parseVariableKey(self.removeExtensions(statements['variable']))

    statements['module'] = self.parseModuleKey(value)

  def onInterprete(self, interpreted, mode=SIMode.REPLACE_MODE):
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

    if mode != SIMode.REPLACE_MODE and interpreted.handler_name == "require" and not "require" in interpreted.simport.context:
      statements["variable"] = statements["module"]
      interpreted.handler_name = "import"

    if self.getSetting("es5") or self.getSetting("require_by_default"):
      if interpreted.handler_name == "import_from":
        interpreted.handler_name = "require_from"
      else:
        interpreted.handler_name = "require"

    return super().onInterprete(interpreted)

  def stringifyStatements(self, statements, handler_name=None, insert_type=Interpreted.IT_REPLACE):
    import_str = ''

    if handler_name.startswith('require'):
      if 'variable' in statements and handler_name != 'require_plain':
        import_str += 'const ' if not self.getSetting("es5") else 'var '
        import_str += statements['variable']
        import_str += ' = '

      if 'module':
        import_str += "require('{0}')".format(statements['module'])

      if self.getSetting("es5") or self.getSetting("add_semicolon"):
        import_str += ';'

    else:
      import_str = 'import '
      if handler_name != "import_pure":
        if handler_name == "import_all_from":
          import_str += "* as "

        if 'variable' in statements:
          import_str += statements['variable']

        if 'submodules' in statements:
          if 'variable' in statements:
            import_str += ', '
          import_str += "{{ {0} }}".format(", ".join(statements['submodules']))

        import_str += " from "

      import_str += "\'{0}\'".format(statements['module'])

      if self.getSetting("add_semicolon"):
          import_str += ';'

    if insert_type == Interpreted.IT_INSERT_AFTER:
      import_str = "\n" + import_str
    elif insert_type == Interpreted.IT_INSERT:
      import_str += "\n"

    return import_str

  def parseBeforeInsert(self, interpreted, view_imports, mode=SIMode.REPLACE_MODE):
    if interpreted.handler_name.startswith('import'):
      regex = r"^{0}({1})?$".format(
        interpreted.statements['module'],
        "|".join(self.getSetting('remove_extensions'))
      )

      for vimport in view_imports:
        if re.search(regex, vimport.statements['module']):
          Handler.joinStatements(vimport.statements, interpreted.statements)
          vimport.insert_type = Interpreted.IT_REPLACE_IMPORT
          return vimport

    if mode == SIMode.PUSH_MODE or mode == SIMode.PANEL_MODE:
      if len(view_imports):
        region_point = view_imports[-1].simport.context_region.end()
        interpreted.insert_type = Interpreted.IT_INSERT_AFTER
        interpreted.simport.region = Region(region_point, region_point)
      else:
        interpreted.insert_type = Interpreted.IT_INSERT

    return interpreted

  def getDictionary(self):
    obj = {}
    dictionary = self.settings['dictionary']
    if dictionary:
      for key in obj:
        obj = { "variable": key, "module": obj[key] }
    return obj

  def parseOptions(self, interpreted, options):
    if 'dictionary' in self.settings:
      for key in self.settings['dictionary']:
        if interpreted.simport.expression == key:
          options['files'].append(self.settings['dictionary'][key])
    return options


