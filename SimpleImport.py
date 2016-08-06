from os import walk
import sublime, sublime_plugin, re, json
from .lib.interpreters import *
from .lib.interpreters import __all__ as InterpretersNames
from .lib.interpreter  import *
from .lib.interpreter import __all__ as interpreter
from os import path

class SimpleImport():
  cachedExports = {}
  interpreters = {}

  @staticmethod
  def getInstalledModules(interpreter, project_path):
    if not interpreter.modules_folder:
      return []

    modules_path = path.join(project_path, interpreter.modules_folder)
    modules_path_len = len(modules_path)
    modules = []

    for dirpath, dirnames, filenames in walk(modules_path, topdown=True):
      relative_path = dirpath[modules_path_len:] if dirpath != project_path else ""
      modules = [ module for module in dirnames if not module[0] == "."]
      break;
    return modules

  @staticmethod
  def normalizeValue(value):
    return re.sub(r"-|\.", "", value).lower()

  @staticmethod
  def findRelatedInstalledModules(value, interpreter, project_path):
    installed_modules = SimpleImport.getInstalledModules(interpreter, project_path)
    value = SimpleImport.normalizeValue(value)
    arr = [ module for module in installed_modules if SimpleImport.normalizeValue(module).startswith(value)]
    arr.sort()
    return arr

  @staticmethod
  def isInstalledModule(value, interpreter, project_path):
    return value in SimpleImport.getInstalledModules(interpreter, project_path)

  @staticmethod
  def loadInterpreters():
    interpreter_regex = r"Interpreter$"
    for name in  InterpretersNames:
      _object = globals()[name]()
      SimpleImport.interpreters[_object.syntax] = _object

  @staticmethod
  def findByValue(value, interpreter, project_path):
    files = []
    extra_files = []
    containing_files = []
    project_path_len = len(project_path)
    regex = "({0}|{0}\/index){1}$".format(value, "(" + "|".join(interpreter.extensions) + ")")

    for dirpath, dirnames, filenames in walk(project_path, topdown=True):
      relative_path = dirpath[project_path_len:]
      dirnames[:] = [dirname for dirname in dirnames if path.join(relative_path, dirname) not in ["node_modules", ".git"]]

      for filename in filenames:

        # Find files with name equal the value
        if re.search(regex, path.join(relative_path, filename), re.IGNORECASE):
          files.append(path.join(relative_path, filename))

        # Find files that export the value
        if True in [ filename.endswith(extension) for extension in interpreter.extensions ]:
          matches = re.findall(r"(export\s+(const|let|var|function|class)\s+(?P<value>[^\s]+))", open(path.join(dirpath, filename)).read())
          for match in matches:
            if match[2] == value:
              containing_files.append(path.join(relative_path, filename))
          pass

        # Find files with name equal the value and extra extension
        if interpreter.extra_extensions and re.search(r"{0}({1})".format(value, "|".join(interpreter.extra_extensions)), filename, re.IGNORECASE):
          extra_files.append(path.join(relative_path, filename))


    response = {}
    response["files"] = files
    response["containing_files"] = containing_files
    response["extra_files"] = extra_files
    return response

  @staticmethod
  def findValueInFiles(project_path, interpreter, value):
    extensions = interpreter.extensions
    containing_files = []
    project_path_len = len(project_path)

    for dirpath, dirnames, filenames in walk(project_path, topdown=True):
      relative_path = dirpath[project_path_len:] if dirpath != project_path else ""
      dirnames[:] = [dirname for dirname in dirnames if ( path.join(relative_path, dirname)  ) not in ["node_modules", ".git"]]

      for filename in filenames:
        for extension in extensions:
          if filename.endswith(extension):
            matches = re.findall(r"(export\s+(const|let|var|function|class)\s+(?P<value>[^\s]+))", open(path.join(dirpath, filename)).read())
            for match in matches:
              if match[2] == value:
                containing_files.append(path.join(relative_path, filename))
          break
    return containing_files

  @staticmethod
  def cacheExports(interpreter):
    open_folders = view.window().folders()
    extensions = interpreter.extensions
    exports_by_folder = {}

    for folder_path in open_folders:
      folder_path_len = len(folder_path)

      for dirpath, dirnames, filenames in walk(folder_path, topdown=True):
        relative_path = dirpath[folder_path_len:] if dirpath != folder_path else ""
        dirnames[:] = [dirname for dirname in dirnames if ( path.join(relative_path, dirname)  ) not in ["node_modules", ".git"]]
        for filename in filenames:
          for extension in extensions:
            if filename.endswith(extension):
              if folder_path not in exports_by_folder:
                exports_by_folder[folder_path] = {}

              matches = re.findall(r"(export\s+(const|let|var|function|class)\s+(?P<value>[^\s]+))", open(path.join(dirpath, filename)).read())

              if len(matches):
                exports_by_folder[folder_path][path.join(relative_path, filename)] = [ match[2] for match in matches ]

              break
    cachedExports[interpreter.syntax] = exports_by_folder

def getInterpreter(syntax):
    for key in SimpleImport.interpreters:
      if re.search(r"^\.?{0}".format(key), syntax, re.IGNORECASE):
        return SimpleImport.interpreters[key]
    return None

# Stands for Simple Selection
class SSelection:
  @staticmethod
  def getExpressionInContext(expression, context):
    match = re.search(r"[^\.;\s]*{0}".format(expression), context)
    if match:
      return match.group(0)
    return expression

  def __init__(self, expression, context, region, context_region, index=0):
    self.expression = self.getExpressionInContext(expression, context)
    self.context = context

    self.index = index
    self.sImports = []
    self.resolved = False

    # Regions
    self.region = region
    self.context_region = context_region

  def addImport(self, sImport):
    self.sImports.append(sImport)

  def resolve(self):
    sef.status = True

  def areImportsPending(self):
    pending = False
    for x in self.sImports:
      if not x.resolved:
        pending = True
        break

    return pending

# ===================================================================

class SimpleImportCommand(sublime_plugin.TextCommand):

  def run(self, edit):

    syntax = path.basename(self.view.settings().get('syntax')).lower()
    self.project_path = self.view.window().folders()[-1]
    self.rel_view_path = path.dirname(self.view.file_name())[len(self.project_path):]
    self.interpreter = getInterpreter(syntax)

    if not self.interpreter:
      print("Simple import does not support '.{0}' syntax yet".format(syntax))
      return

    selections = self.view.sel()
    selection_index = 0
    self.all_imports = self.findAllImports()
    self.final_imports = []

    for selection in selections:
      if selection.end() == selection.begin():
        region = self.view.word(selection)
        context_region = sublime.Region(self.view.line(selection).begin(), region.end())
      else:
        region = selection
        context_region = selection

      # expression, context, region, context_region, index
      sSelection = SSelection(
        self.view.substr(region),
        self.view.substr(context_region),
        region,
        context_region,
        selection_index
      )

      interpreted = self.interpreter.interprete(sSelection)
      self.interpreted = interpreted

      file_query_value = self.interpreter.getFileQuery(interpreted)
      module_query_value = self.interpreter.getModuleQuery(interpreted)

      interpreted.options = SimpleImport.findByValue(file_query_value, self.interpreter, self.project_path)
      interpreted.options["modules"] = SimpleImport.findRelatedInstalledModules(module_query_value, self.interpreter, self.project_path)

      options_arr = interpreted.getOptionsArr()


      if len(options_arr) == 1:
        self.handleOptionClick(0)
      elif len(options_arr) > 1:
        self.view.show_popup_menu(options_arr, self.handleOptionClick)

      #self.view.run_command("replace", {"characters": result.__str__(), "start": result.region.begin(), "end": result.region.end()})
      #

  def parsePath(self, path):
    if path[:2] == "./" or path[:3] == "../":
      return path
    else:
      return "./" + path

  def handleOptionClick(self, index):
    if index != -1:
      option_obj = self.interpreted.getOptionObjectByIndex(index)

      if option_obj["key"] != "modules":
        option_obj["value"] = self.parsePath(path.normpath(path.relpath("/" + option_obj["value"], self.rel_view_path)))

      self.interpreter.setStatementsByOption(self.interpreted, option_obj)
      statements = self.interpreted.statements

      regex = self.interpreter.getComparatorRegex(statements)
      found = False
      for _import in self.all_imports:
        _import_statements = _import[0]

        if self.interpreter.compareStatements(_import_statements, regex=regex):
          found = True
          for key in statements:
            if not key in _import_statements:
              _import_statements[key] = statements[key]
              pass

            if type(_import_statements[key]) is list:
              _import_statements[key] = _import_statements[key] + list(set(statements[key]) - set(_import_statements[key]))
            else:
              _import_statements[key] = statements[key]
          self.final_imports.append((_import[0], _import[1], "replace"))
          break

      if not found:
        if len(self.all_imports):
          insert_type = "insert_after"
          end = self.all_imports[-1][1].end()
        else:
          insert_type = "insert"
          end = 0
        self.final_imports.append((statements, sublime.Region(end, end), insert_type))

      self.writeFinalImports()

  def writeFinalImports(self):
    for _import in self.final_imports:
      self.view.run_command("replace", {
        "characters": self.interpreter.parseStatementsToString(_import[0], insert_type=_import[2]),
        "start": _import[1].begin(),
        "end": _import[1].end()
      })

  def findAllImports(self):
    regions = self.view.find_all(self.interpreter.find_imports_regex)
    return [ (self.interpreter.parseStringToImport(self.view.substr(region)), region) for region in regions ]



class ReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit, characters, start=0, end=False):
      if(end == False and end != 0):
        end = self.view.size()
      self.view.replace(edit,sublime.Region(start, end), characters)

SimpleImport.loadInterpreters()
