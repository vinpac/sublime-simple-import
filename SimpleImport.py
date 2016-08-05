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
    modules_path = path.join(project_path, interpreter.modules_folder)
    modules_path_len = len(modules_path)
    modules = []

    for dirpath, dirnames, filenames in walk(modules_path, topdown=True):
      relative_path = dirpath[modules_path_len:] if dirpath != project_path else ""
      modules = [ module for module in dirnames if not module[0] == "."]
      break;
    return modules

  @staticmethod
  def isInstalledModule(module, interpreter, project_path):
    return module in SimpleImport.getInstalledModules(interpreter, project_path)

  @staticmethod
  def loadInterpreters():
    interpreter_regex = r"Interpreter$"
    for name in  InterpretersNames:
      _object = globals()[name]()
      SimpleImport.interpreters[_object.syntax] = _object

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
  def __init__(self, expression, context, region, context_region, index=0):
    self.expression = expression
    self.context = context
    self.expression_in_context = self.getExpressionInContext()

    self.index = index
    self.sImports = []
    self.resolved = False

    # Regions
    self.region = region
    self.context_region = context_region

  def getExpressionInContext(self):
    match = re.search(r"[^\.;\s]*{0}".format(self.expression), self.context)
    if match:
      return match.group(0)
    return expression

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

class SimpleImportInterpretersCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    SimpleImport.loadInterpreters()
    print("Interpreters reloaded")

# ===================================================================
class SimpleImportEventListener(sublime_plugin.EventListener):
  def on_post_save(self, view):
    syntax = path.basename(view.settings().get('syntax')).lower()
    self.interpreter = getInterpreter(syntax)

    if not self.interpreter:
      print("Simple import does not support '.{0}' syntax yet".format(syntax))
      return


    # TODO: find every export in the current file and store it in json file
    # with filepath as the key
    #
    # matches = view.find_all(r"(export\s+(const|let|var|function|class|default)\s+[^\s]+)")
    # for region in matches:
    #   print(view.substr(region).split(" ")[-1])



# ===================================================================

class SimpleImportCommand(sublime_plugin.TextCommand):

  def run(self, edit):

    syntax = path.basename(self.view.settings().get('syntax')).lower()
    self.interpreter = getInterpreter(syntax)

    if not self.interpreter:
      print("Simple import does not support '.{0}' syntax yet".format(syntax))
      return

    selections = self.view.sel()
    selection_index = 0


    for selection in selections:
      region = self.view.word(selection)
      context = sublime.Region(self.view.line(selection).begin(), region.end())

      # expression, context, region, context_region, index
      sSelection = SSelection( self.view.substr(region), self.view.substr(context), region, context, selection_index )

      sImport = self.interpreter.resolve(sSelection)
      #print(sImport.__str__())
      #print(sSelection.context)
      print(SimpleImport.findValueInFiles(self.view.window().folders()[1], self.interpreter, sImport.statements['variable']))
      print(SimpleImport.isInstalledModule(sImport.statements['module'], self.interpreter, self.view.window().folders()[1]))

      #self.view.run_command("replace", {"characters": result.__str__(), "start": result.region.begin(), "end": result.region.end()})


  def handle(self):
    print("handle")


class ReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit, characters, start=0, end=False):
      if(end == False):
        end = self.view.size()
      self.view.replace(edit,sublime.Region(start, end), characters)

SimpleImport.loadInterpreters()
