import re
from .utils import endswith
from os import walk, path
from .interpreters import *
from .interpreters import __all__ as InterpretersNames

class SimpleImport():
  interpreters = {}

  @staticmethod
  def loadInterpreters():
    interpreter_regex = r"Interpreter$"
    for name in  InterpretersNames:
      _object = globals()[name]()
      SimpleImport.interpreters[_object.syntax] = _object

  def getInterpreter(syntax, view_filename):
    for key in SimpleImport.interpreters:
      if re.search(r"^\.?{0}".format(key), syntax, re.IGNORECASE):
        return SimpleImport.interpreters[key]
    return None

  @staticmethod
  def findAll(interpreter, project_path, include_extras=False):
    files = []
    extra_files = []
    extensions = interpreter.getSetting('extensions', [])
    extra_extensions = interpreter.getSetting('extra_extensions', [])
    excluded_paths = [ path.normpath(epath) for epath in interpreter.getSetting("excluded_paths", []) ]

    for dirpath, dirnames, filenames in walk(project_path, topdown=True):
      relative_dir = path.relpath(dirpath, project_path)
      dirnames[:] = [dirname for dirname in dirnames if path.normpath(path.join(relative_dir, dirname)) not in excluded_paths]
      for filename in filenames:
        if endswith(extensions, filename):
          files.append(path.join(relative_dir, filename))
          continue

        if endswith(extra_extensions, filename):
          extra_files.append(path.join(relative_dir, filename))
    return {
      "files": files,
      "extra_files": extra_files,
      "modules": SimpleImport.findAllModules(interpreter, project_path)
    }

  @staticmethod
  def findAllModules(interpreter, project_path):
    if not interpreter.getSetting('modules_folder'):
      return []

    modules_path = path.join(project_path, interpreter.getSetting('modules_folder'))
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
    if not value:
      return []

    installed_modules = SimpleImport.findAllModules(interpreter, project_path)
    value = SimpleImport.normalizeValue(value)
    arr = [ module for module in installed_modules if SimpleImport.normalizeValue(module) == value ]
    arr.sort()
    return arr

  @staticmethod
  def isInstalledModule(value, interpreter, project_path):
    return value in SimpleImport.findAllModules(interpreter, project_path)

  @staticmethod
  def findByValue(interpreter, project_path, filename_query=None, containing_query=None, exclude_file=None):
    regex = interpreter.getFileQueryRegex(filename_query)
    regex_extra_files = interpreter.getExtraFileQueryRegex(filename_query)
    extensions = interpreter.getSetting('extensions')
    excluded_paths = [ path.normpath(epath) for epath in interpreter.getSetting("excluded_paths", ['.git']) ]
    result = {
      "files": [],
      "containing_files": [],
      "extra_files": []
    }

    for dirpath, dirnames, filenames in walk(project_path, topdown=True):
      relative_dir = path.relpath(dirpath, project_path)
      # Change excluding folders
      dirnames[:] = [dirname for dirname in dirnames if path.normpath(path.join(relative_dir, dirname)) not in excluded_paths]
      for filename in filenames:
        if exclude_file == path.join(relative_dir, filename):
          continue

        # Find files with name equal the value
        if re.search(regex, path.join(relative_dir, filename), re.IGNORECASE):
          result["files"].append(path.join(relative_dir, filename))
        else:
          if regex_extra_files and re.search(regex_extra_files, path.join(relative_dir, filename), re.IGNORECASE):
            result["extra_files"].append(path.join(relative_dir, filename))
            pass

        if containing_query:
          # Find files that export the value
          if endswith(extensions, filename):
            try:
              matches = re.findall(interpreter.find_exports_regex, open(path.join(dirpath, filename)).read())
              for match in matches:
                if match[2] == containing_query:
                  result["containing_files"].append(path.join(relative_dir, filename))
            except IOError:
              print("SimpleImport: Could not read", path.join(dirpath, filename))

    return result

  @staticmethod
  def query (query, interpreter, project_path, exclude=None):
    if not query:
      return {}

    if type(query) is str:
      query = {
        "file": query,
        "containing": query,
        "module": query
      }
    result = SimpleImport.findByValue(
      interpreter,
      project_path,
      filename_query=(query['file'] if 'file' in query else None),
      containing_query=(query['containing'] if 'containing' in query else None),
      exclude_file=exclude
    )
    result["modules"] = SimpleImport.findRelatedInstalledModules(
      query['module'] if 'module' in query else None,
      interpreter,
      project_path
    )

    return result
