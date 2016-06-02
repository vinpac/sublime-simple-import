import sublime, sublime_plugin, re, json
from .lib.interpreters import *
from .lib.interpreters import __all__ as InterpretersNames
from .lib.interpreter  import *
from .lib.interpreter import __all__ as interpreter
from os import path

# Stands for Simple Selection
class SSelection:
  def __init__(self, expression, context, region, context_region, index=0):
    self.expression = expression
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

class SimpleImport():
  interpreters = {}
  @staticmethod
  def loadInterpreters():
    interpreter_regex = r"Interpreter$"
    for name in  InterpretersNames:
      _object = globals()[name]()
      SimpleImport.interpreters[_object.syntax] = _object

# ===================================================================

class SimpleImportInterpretersCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    SimpleImport.loadInterpreters()
    print("Interpreters reloaded")


# ===================================================================

class SimpleImportCommand(sublime_plugin.TextCommand):

  def run(self, edit):

    syntax = path.basename(self.view.settings().get('syntax')).lower()
    self.interpreter = self.getInterpreter(syntax)

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
      print(sImport.__str__())

      #self.view.run_command("replace", {"characters": result.__str__(), "start": result.region.begin(), "end": result.region.end()})


  def handle(self):
    print("handle")

  def getInterpreter(self, syntax):
    print(SimpleImport.interpreters)
    for key in SimpleImport.interpreters:
      if re.search(r"^\.?{0}".format(key), syntax, re.IGNORECASE):
        return SimpleImport.interpreters[key]
    return None


class ReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit, characters, start=0, end=False):
      if(end == False):
        end = self.view.size()
      self.view.replace(edit,sublime.Region(start, end), characters)

SimpleImport.loadInterpreters()
