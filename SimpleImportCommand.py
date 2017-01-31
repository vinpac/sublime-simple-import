import sublime, sublime_plugin, re, json
from os import path
from .lib.interpreters import *
from .lib.interpreter.SImport import SImport
from .lib.interpreter.Interpreted import Interpreted
from .lib.interpreter.PendingImport import PendingImport
from .lib.interpreters import __all__ as InterpretersNames
from .lib.SIMode import SIMode

class SimpleImportCommand(sublime_plugin.TextCommand):
  SETTINGS_FILE = ".simple-import.json"
  interpreters = {}

  @staticmethod
  def loadInterpreters():
    interpreter_regex = r"Interpreter$"
    for name in InterpretersNames:
      obj = globals()[name]()
      SimpleImportCommand.interpreters[obj.syntax] = obj

  @staticmethod
  def getInterpreter(view_syntax, view_filename):
    for key in SimpleImportCommand.interpreters:
      if SimpleImportCommand.interpreters[key].isCompatibleView(
        view_filename,
        view_syntax
      ):
        return SimpleImportCommand.interpreters[key]

    return None

  def run(self, edit, push_mode=False, panel_mode=False):
    # modes
    self.mode = SIMode.REPLACE_MODE
    if push_mode:
      self.mode = SIMode.PUSH_MODE
    elif panel_mode:
      self.mode = SIMode.PANEL_MODE

    # paths
    self.view_path = path.dirname(self.view.file_name())
    self.project_path = self.getProjectFolder()
    self.view_dir_relpath = path.relpath(self.view_path, self.project_path)
    self.view_filename = path.basename(self.view.file_name())
    self.view_relpath = path.join(self.view_dir_relpath, self.view_filename)
    view_syntax = path.basename(self.view.settings().get('syntax')).lower()

    self.interpreter = SimpleImportCommand.getInterpreter(
      view_syntax,
      self.view_filename
    )

    if not self.interpreter:
      print("Simple import does not support '.{0}' syntax yet".format(view_syntax))
      return

    self.loadSettings()

    selections = self.view.sel()
    self.view_imports = self.findAllImports()
    self.interpreted_list = []
    self.pending_imports = []
    self.imports_to_insert = []

    for selection in selections:
      if selection.end() == selection.begin():
        region = self.view.word(selection)
        context_region = sublime.Region(self.view.line(selection).begin(), region.end())
      else:
        region = selection
        context_region = selection

      simport = SImport(
        # expression
        self.view.substr(region),
        # context
        self.view.substr(context_region),
        region,
        context_region
      )

      if not self.isPanelMode() and not len(simport.expression.strip()):
        continue

      interpreted = self.interpreter.interprete(simport, mode=self.mode)
      self.interpreted_list.append(interpreted)
      pending_import = None

      if self.isPanelMode():
        pending_import = PendingImport(
          interpreted,
          self.interpreter.findByValue(
            '',
            self.project_path,
            omit_files=[path.join(self.view_relpath)]
          )
        )

        self.view.window().show_quick_panel(
          pending_import.getOptionsAsList(),
          self.onOptionSelected
        )
      else:
        queryValue = self.interpreter.getQueryValue(interpreted)

        if queryValue != False:
          pending_import = PendingImport(
            interpreted,
            self.interpreter.findByValue(
              queryValue,
              self.project_path,
              omit_files=[path.join(self.view_relpath)]
            )
          )

      if pending_import:
        self.pending_imports.append(pending_import)

      if self.isPanelMode():
        return

    for pending_import in self.pending_imports:
      options_arr = pending_import.getOptionsAsList(include_keys=True)

      if len(options_arr) > 1:
        self.view.show_popup_menu(options_arr, self.onOptionSelected)
      else:
        self.onOptionSelected(0)

  def onOptionSelected(self, index):
    for pending_import in self.pending_imports:
      if not pending_import.resolved:
        pending_import.resolved = True
        if index != -1:
          option_obj = self.interpreter.parseOptionItem(
            pending_import.getOptionByIndex(index),
            self.view_dir_relpath
          )

          if not option_obj:
            break

          self.interpreter.onSearchResultChosen(
            pending_import.interpreted,
            option_obj['key'],
            option_obj['value'],
            mode=self.mode
          )
        else:
          self.pending_imports.remove(pending_import)
          self.interpreted_list.remove(pending_import.interpreted)

        break

    if False not in [ pending.resolved for pending in self.pending_imports ]:
      self.onPendingImportsResolved()

  def onPendingImportsResolved(self):
    for interpreted in self.interpreted_list:
      resolved = self.interpreter.parseBeforeInsert(
        interpreted,
        self.view_imports,
        mode=self.mode
      )

      if isinstance(resolved, list):
        for vimport in resolved:
          if vimport not in self.imports_to_insert:
            self.imports_to_insert.append(vimport)
      elif resolved not in self.imports_to_insert:
        self.imports_to_insert.append(resolved)

    for interpreted in self.imports_to_insert:
      self.handleInsertion(interpreted)

  def handleInsertion(self, interpreted):
    if interpreted.insert_type == Interpreted.IT_INSERT:
      self.view.run_command("insert_at", {
        "characters": interpreted.__str__()
      })
    else:
      self.view.run_command("replace", {
        "characters": interpreted.__str__(),
        "start": interpreted.simport.region.begin(),
        "end": interpreted.simport.region.end()
      })

  def findAllImports(self):
    if not self.interpreter.find_imports_regex:
      return []

    regions = self.view.find_all(self.interpreter.find_imports_regex)
    return [
      self.interpreter.interprete(
        SImport(
          self.view.substr(region),
          self.view.substr(region),
          region,
          region
        ),
        mode=self.mode
      )
      for region in regions
    ]

  def isPanelMode(self):
    return self.mode == SIMode.PANEL_MODE

  def getProjectFolder(self):
    folders = self.view.window().folders()
    for folder in folders:
      if self.view_path.startswith(folder):
        return folder
    return folders[0]

  def getProjectSettings(self):
    SETTINGS_FILE = SimpleImportCommand.SETTINGS_FILE

    if path.isfile(path.join(self.project_path, SETTINGS_FILE)):
      with open(path.join(self.project_path, SETTINGS_FILE)) as raw_json:
        try:
          settings_json = json.load(raw_json)
          if self.interpreter.syntax in settings_json:
            settings = settings_json[self.interpreter.syntax]
            if "$path" in settings:
              settings_on_file = {}
              for match in settings["$path"]:
                if len(match) == 1:
                  settings_on_file.update(match[0])
                else:
                  pattern = '|'.join(match[:-1])
                  if re.search("^{0}".format(pattern), self.view_relpath):
                    settings_on_file.update(match[-1])
              return settings_on_file
            else:
              return settings_json[self.interpreter.syntax]
        except ValueError:
          print("Failed to load .simple-import.json at {0}".format(self.project_path))

  def loadSettings(self):
    settings = {}

    view_settings = self.view.settings().get("simple-import")
    if view_settings and self.interpreter.syntax in view_settings:
      settings.update(view_settings[self.interpreter.syntax])

    project_settings = self.getProjectSettings()
    if project_settings:
      settings.update(project_settings)

    # Copy default settings and update with new settings
    # so settings won't stick through different evironments
    obj = self.interpreter.settings.copy()
    obj.update(settings)

    rulers = self.view.settings().get("rulers") or []

    # Find the smallest ruler
    for x in rulers:
      if 'ruler' in obj:
        if x < obj['ruler']:
          obj['ruler'] = x
      else:
        obj['ruler'] = x

    self.interpreter.setSettings(obj)

class ReplaceCommand(sublime_plugin.TextCommand):
  def run(self, edit, characters, start=0, end=False):
    if(end == False and end != 0):
      end = self.view.size()
    self.view.replace(edit,sublime.Region(start, end), characters)

class InsertAtCommand(sublime_plugin.TextCommand):
  def run(self, edit, characters, start=0):
    self.view.insert(edit, start, characters)

SimpleImportCommand.loadInterpreters()
