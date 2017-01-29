import re, json
from sublime import Region
from os import path, walk
from ..utils import joinStr, endswith
from ..interpreter import *
from ..SIMode import SIMode

class JavascriptInterpreter(Interpreter):

  cachedModules = {}

  def run(self):

    self.find_imports_regex = r"(import[\s\n]+((?:(?!from|;)[\s\S])*)[\s\n]+from[\s]+[\"\']([^\"\']+)[\"\'](;?))"
    self.find_exports_regex = r"(export\s+(const|let|var|function|class)\s+(?P<value>[\w]+)|exports\.(?P<value2>[\w]+)\s*=)"

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

    # Remove last submodule if empty
    if len(submodules) and submodules[-1].strip() == '':
      submodules.pop()

    return [ submodule.strip() for submodule in submodules ]

  def parseVariableKey(self, value):
    return joinStr(re.sub(r"!|@|\*", "", value), r"\/|-|\.")

  def getQueryValue(self, interpreted):
    return interpreted.statements["module"]

  def onSearchResultChosen(self, interpreted, option_key, value, mode=SIMode.REPLACE_MODE):
    statements = interpreted.statements
    if ((mode == SIMode.PANEL_MODE and len(statements['variable'])) or
      option_key in ["exports", "module_exports"]
    ):
      interpreted.handler_name = "import_from"
      statements['submodules'] = self.parseSubmodulesKey(
        interpreted.statements['variable']
      )
      del statements['variable']
    elif mode == SIMode.PANEL_MODE:
      if option_key != "modules":
        statements['variable'] = path.basename(value)
      else:
        statements['variable'] = value

      statements['variable'] = self.parseVariableKey(
        self.removeExtensions(statements['variable'])
      )

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
    shouldAddSubmodules = False
    import_str = ''
    statements_length = len(statements)

    if statements_length < 3:
      if "submodules" in statements:
        if not len(statements["submodules"]):
          return import_str
      elif statements_length == 1:
        return import_str

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

          shouldAddSubmodules = True
          statements['submodules'].sort()
          import_str += "{{{SI_SUBMODULES}}}"

        import_str += " from "

      import_str += "\'{0}\'".format(statements['module'])

      if self.getSetting("add_semicolon"):
          import_str += ';'

    if insert_type == Interpreted.IT_INSERT_AFTER:
      import_str = "\n" + import_str
    elif insert_type == Interpreted.IT_INSERT:
      import_str += "\n"

    if shouldAddSubmodules:
      import_str_with_subs = import_str.format(SI_SUBMODULES=" " + ", ".join(
        statements['submodules']
      ) + " ")

      ruler = self.getSetting('ruler')
      if ruler and len(import_str_with_subs) > ruler:
        import_str = import_str.format(SI_SUBMODULES="\n\t" + ",\n\t".join(
          statements['submodules']
        ) + ",\n")
      else:
        import_str = import_str_with_subs

    return import_str

  def parseBeforeInsert(self, interpreted, view_imports, mode=SIMode.REPLACE_MODE):
    modifiedImports = []
    shouldAppendInterpreted = True

    if interpreted.handler_name.startswith('import'):
      regex = r"^{0}({1})?$".format(
        interpreted.statements['module'],
        "|".join(self.getSetting('remove_extensions'))
      )

      for vimport in view_imports:
        shouldAdjustRegion = False

        if vimport.statements['module'] == interpreted.statements['module']:
          Handler.joinStatements(vimport.statements, interpreted.statements)
          vimport.insert_type = Interpreted.IT_REPLACE_IMPORT

          modifiedImports.append(vimport)
          shouldAppendInterpreted = False
          shouldAdjustRegion = True
        elif 'submodules' in interpreted.statements:
          for submodule in interpreted.statements['submodules']:
            if 'submodules' in vimport.statements:
              if submodule in vimport.statements['submodules']:
                vimport.statements['submodules'].remove(submodule)

              if (not len(vimport.statements['submodules']) and
                'variable' not in vimport.statements
              ):
                vimport.remove()

              modifiedImports.append(vimport)
              shouldAdjustRegion = True

        if shouldAdjustRegion:
          # Adjust region
          for modifiedImport in modifiedImports:
            context_region = modifiedImport.simport.context_region
            if context_region.end() < vimport.simport.context_region.begin():
              # New length minus initial length
              import_text = modifiedImport.__str__()
              newLength = len(import_text) + max(0, import_text.count("\n") - 1)
              initialLength = context_region.end() - context_region.begin()
              lengthDiff = newLength - initialLength

              new_region = Region(
                vimport.simport.context_region.begin() + lengthDiff,
                vimport.simport.context_region.end() + lengthDiff
              )

              vimport.simport.context_region = new_region
              vimport.simport.region = new_region

    if mode == SIMode.PUSH_MODE or mode == SIMode.PANEL_MODE:
      interpreted.insert_type = Interpreted.IT_INSERT

      if len(view_imports):
        lastImport = view_imports[-1]

        if lastImport:
          context_region = vimport.simport.context_region
          if vimport in modifiedImports:
            # New length minus initial length
            vimport_str = vimport.__str__()
            newLength = len(vimport_str) + max(0, vimport_str.count("\n") - 1)
            initialLength = context_region.end() - context_region.begin()
            lengthDiff = newLength - initialLength

            region_begin = context_region.end() + lengthDiff
            region_end = region_begin
          else:
            region_begin = context_region.end()
            region_end = region_begin

          if vimport.removed:
            interpreted.insert_type = Interpreted.IT_REPLACE
          else:
            interpreted.insert_type = Interpreted.IT_INSERT_AFTER

          interpreted.simport.region = Region(region_begin, region_end)

    if shouldAppendInterpreted:
      modifiedImports.append(interpreted)

    return modifiedImports

  def getDictionary(self):
    obj = {}
    dictionary = self.settings['dictionary']
    if dictionary:
      for key in obj:
        obj = { "variable": key, "module": obj[key] }
    return obj

  def findAllModules(self, project_path):
    modules = []
    if path.isfile(path.join(project_path, 'package.json')):
      with open(path.join(project_path, 'package.json')) as raw_json:
        try:
          packageJson = json.load(raw_json)
          for key in [
            "dependencies",
            "devDependencies",
            "peerDependencies",
            "optionalDependencies"
          ]:
            if key in packageJson:
              modules += packageJson[key].keys()

        except ValueError:
          SimpleImport.log_error("Failed to load package.json at {0}".format(
            self.project_path
          ))

    return modules


  def buildRegexForModule(self, value):
    return r"(^{0}$)".format(self.normalizeValue(value))

  def findInDictionary(self, value, defaultResult={}):
    result = defaultResult
    dictionary = self.getSetting('dictionary')

    if not dictionary:
      return result

    # Find modules containing value
    if "modules" in dictionary:
      for module in dictionary["modules"]:
        if value in dictionary["modules"][module]:
          if "module_exports" not in result:
            result["module_exports"] = {}

          if module not in result["module_exports"]:
            result["module_exports"][module] = []

          if value not in result["module_exports"][module]:
            result["module_exports"][module].append(value)

    return result

  def findByValue(self, value, project_path, omit_files=None):
    return self.findInCachedModules(
      value,
      project_path,
      defaultResult=self.findInDictionary(
        value,
        defaultResult=self.findByValueInProject(
          value,
          project_path,
          omit_files=omit_files
        )
      )
    )

  def findByValueInProject(self, value, project_path, omit_files=None):
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

        # Find files that export the value
        if self.isValidFile(filename):
          try:
            matches = re.findall(
              self.find_exports_regex,
              open(path.join(dirpath, filename)).read()
            )

            for match in matches:
              match_value = match[2] if match[2] else match[3]

              if match_value == value:
                file_path = path.join(relative_dir, filename)

                if "exports" not in result:
                  result["exports"] = {}

                if file_path not in result["exports"]:
                  result["exports"][file_path] = []

                result["exports"][file_path].append(
                  match_value
                )
          except IOError:
            print("SimpleImport: Could not read", path.join(dirpath, filename))

    return result

  def findInCachedModules(self, value, project_path, defaultResult={}):
    regex_for_modules = self.buildRegexForModule(value)
    regex_for_files = self.buildRegexForFiles(value)
    regex_for_extra_files = self.buildRegexForExtraFiles(value)

    result = defaultResult
    modules = self.findAllModules(project_path)
    cachedModules = JavascriptInterpreter.cachedModules

    for module in modules:
      if re.search(regex_for_modules, self.normalizeValue(module)):
        if "modules" not in result:
          result["modules"] = []

        result["modules"].append(module)

    self.cacheModules(project_path)

    for moduleName in cachedModules:
      module = cachedModules[moduleName]

      if 'exports' in module and value in module['exports']:
        if "module_exports" not in result:
          result["module_exports"] = {}

        if moduleName not in result["module_exports"]:
          result["module_exports"][moduleName] = []

        result["module_exports"][moduleName].append(value)

      if 'files' in module:
        for filename in module['files']:
          if self.matchFilePathWithRegex(
            filename, regex_for_files, dirpath=moduleName
          ):
            if "module_files" not in result:
              result["module_files"] = []

            result["module_files"].append(path.join(moduleName, filename))

      if 'extra_files' in module:
        for filename in module['extra_files']:
          if self.matchFilePathWithRegex(
            filename, regex_for_files, dirpath=moduleName, is_extra=True
          ):
            if "module_extra_files" not in result:
              result["module_extra_files"] = []

            result["module_extra_files"].append(path.join(moduleName, filename))

    return result


  def cacheModules(self, project_path):
    regex_endswith_index = r"index({0})$".format('|'.join(
      self.getSetting('extensions'))
    )
    cachedModules = JavascriptInterpreter.cachedModules
    modules = self.findAllModules(project_path)

    for moduleName in modules:
      isCached = False
      module_path = path.join(project_path, 'node_modules', moduleName)

      if path.isfile(path.join(module_path, 'package.json')):
        with open(path.join(module_path, 'package.json')) as raw_json:
          try:
            packageJson = json.load(raw_json)
            if "version" in packageJson:
              if (
                moduleName not in cachedModules or
                cachedModules[moduleName]["version"] != packageJson["version"]
              ):
                cachedModules[moduleName] = {
                  "version": packageJson["version"]
                }
              else:
                isCached = True


            # Find exports in the main file
            if not isCached and "main" in packageJson:
              main_file_path = path.join(module_path, packageJson['main'])
              exists = path.isfile(main_file_path)

              # Try with first letter in uppercase
              if not exists:
                main_dir_path = path.dirname(packageJson['main'])
                filename = path.basename(packageJson['main'])

                main_file_path = path.join(
                  module_path,
                  main_dir_path,
                  filename[0].upper() + filename[1:]
                )

                exists = path.isfile(main_file_path)

              if exists:
                matches = re.findall(
                  self.find_exports_regex,
                  open(main_file_path).read()
                )

                for match in matches:
                  match_value = match[2] if match[2] else match[3]
                  if match_value:
                    if "exports" not in cachedModules[moduleName]:
                      cachedModules[moduleName]["exports"] = []

                    cachedModules[moduleName]["exports"].append(match_value)

          except FileNotFoundError:
            print('Error')

      if not isCached:
        for dirpath, dirnames, filenames in walk(module_path, topdown=True):
          for filename in filenames:
            # Find files with name equal the value
            if endswith(self.getSetting('extensions'), filename):
              if re.search(regex_endswith_index, filename):
                continue

              if "files" not in cachedModules[moduleName]:
                cachedModules[moduleName]["files"] = []

              cachedModules[moduleName]["files"].append(filename)
            elif endswith(self.getSetting('extra_extensions'), filename):
              if "extra_files" not in cachedModules[moduleName]:
                cachedModules[moduleName]["extra_files"] = []

              cachedModules[moduleName]["extra_files"].append(filename)
          break
