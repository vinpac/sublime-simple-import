import re
from ..interpreter import *
from ..utils import joinStr

class JavascriptInterpreter(Interpreter):

  find_imports_regex = r"(import[\s\n]+((?:(?!from)[\s\S])*)[\s\n]+from[\s]+[\"\']([^\"\']+)[\"\'])"

  def __init__(self):
    keys = {
      "variable": "[^\s]+",
      "module": "[^\s]+",
      "submodules": "[^\s]+"
    }

    self.syntax = "javascript"
    self.remove_extensions = [".js", ".jsx"]
    self.extensions = [".js", ".jsx"]
    self.extra_extensions = [ ".jpg", ".svg", ".json", ".gif", ".css", ".scss", ".less" ]
    self.modules_folder = 'node_modules'

    self.exports = [
      "export (const|let|var|function|class) {value}",
      "export {\s*{values}\s*}",
      "exports\.{value} ="
    ]

    self.handlers = [
      Handler(
        name="import_all_from",
        matchers=[
          "import {variable}\.\*",
          "{variable}\.\*"
        ],
        keys=keys,
        force=True
      ),
      Handler(
        name="import_from_prefixed",
        matchers=[
          "import {submodules}\.{module}"
        ],
        keys=keys,
        force=True
      ),
      Handler(
        name="require_from",
        matchers=[
          "require {module}\.{submodules}",
          "{module}::{submodules}",
          "extends {module}\.{submodules}"
        ],
        keys=keys
      ),
      Handler(
        name="import_from",
        matchers=[
          "{module}::{submodules}"
        ],
        keys=keys
      ),
      Handler(
        name="import",
        matchers=[
          "{variable}\.{submodules}",
          "import {variable}",
          "(?P<module>[^\s\.]+)(\.[^\s]+){2,}",
          "import {variable} from {module}"
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

  def parseModuleKey(self, value):
    for ext in self.remove_extensions:
      if value.endswith(ext):
        return value[0:-len(ext)]
    return value

  def parseSubmodulesKey(self, value):
    submodules = value.split(',')
    return [ submodule.strip() for submodule in submodules ]

  def parseVariableKey(self, value):
    return joinStr(re.sub(r"!|@|\*", "", value), r"\/|-|\.")

  def getFileQuery(self, interpreted):
    return interpreted.statements["module"]

  def getModuleQuery(self, interpreted):
    return interpreted.statements["module"]

  def setStatementsByOption(self, interpreted, option_obj):
    if option_obj["key"] == "containing_files":
      interpreted.handler = self.handlers[3]
      interpreted.statements['submodules'] = self.parseSubmodulesKey(interpreted.statements['variable'])
      del interpreted.statements['variable']

    interpreted.statements['module'] = self.parseModuleKey(option_obj['value'])

  def onInterprete(self, interpreted):

    if len(interpreted.statements.keys()) == 0:
      index = 0
      keys = ["module", "variable"]
      values = interpreted.sSelection.expression.split(":")
      length = len(values)

      for key in keys:
        interpreted.statements[key] = values[index]
        index += min(index + 1, length - 1)
    else:
      if "module" not in interpreted.statements:
        interpreted.statements["module"] = interpreted.statements["variable"]

    return super().onInterprete(interpreted)

  def parseStringToImport(self, import_str):
    splited = re.search(self.find_imports_regex, import_str).groups()

    import_dict = { "module": splited[2]}

    if "{" not in splited[1]:
      import_dict["variable"] = splited[1]
    else:
      if splited[1][0] == "{" and splited[1][-1] == "}":
        submodules = splited[1][1:-1].split(",")
      else:
        regex = r"\{([^;]*)\}"
        matches = re.search(regex, splited[1]).groups()
        submodules = []
        for match in matches:
          submodules += submodules + match.split(",")
        import_dict["variable"] = re.sub(regex + "|,", '', splited[1]).strip()

      import_dict["submodules"] = [submodule.strip() for submodule in submodules]

    return import_dict

  def parseStatementsToString(self, statements, import_type=None, insert_type="insert"):
    import_str = 'import '

    if import_type:
      if import_type == "import_all_from":
        import_str += "* as "

    if 'variable' in statements:
      import_str += statements['variable']

    if 'submodules' in statements:
      if 'variable' in statements:
        import_str += ', '
      import_str += "{{ {0} }}".format(", ".join(statements['submodules']))

    import_str += " from \'{0}\'".format(statements['module'])

    print(insert_type)
    if insert_type == "insert_after":
      import_str = "\n" + import_str
    elif insert_type == "insert":
      import_str = import_str + "\n"


    return import_str

  def getComparatorRegex(self, statements):
    return r"{0}({1})?$".format(statements['module'], "|".join(self.remove_extensions))

  def compareStatements(self, first_statements, second_statements=None, regex=None):
    if not regex:
      if not second_statements:
        return first_statements == second_statements
      regex = self.getComparatorRegex(second_statements)

    print(regex, first_statements['module'])
    return re.search(regex, first_statements['module'])
