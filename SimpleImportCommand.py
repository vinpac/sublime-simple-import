import sublime, sublime_plugin, re, json
from os import path
from .lib.interpreter.SImport import SImport
from .lib.interpreter.Interpreted import Interpreted
from .lib.interpreter.PendingImport import PendingImport
from .lib.SimpleImport import SimpleImport
from .lib.SIMode import SIMode

class SimpleImportCommand(sublime_plugin.TextCommand):

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

    self.interpreter = SimpleImport.getInterpreter(
      # Selected syntax
      view_syntax,
      # Filename
      self.view_filename
    )

    if not self.interpreter:
      SimpleImport.log_error("Simple import does not support '.{0}' syntax yet".format(view_syntax))
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


      if self.isPanelMode():
        pending_import = PendingImport(
          interpreted,
          SimpleImport.findAll(
            self.interpreter,
            self.project_path
          )
        )

        self.view.window().show_quick_panel(
          pending_import.getOptionsArr(),
          self.onOptionSelected
        )
      else:
        query = self.interpreter.getQueryObject(interpreted)

        if query != False:
          pending_import = PendingImport(
            interpreted,
            SimpleImport.query(
              query,
              self.interpreter,
              self.project_path,
              exclude=path.join(self.view_relpath)
            )
          )

      self.pending_imports.append(pending_import)

      if self.isPanelMode():
        return

    for pending_import in self.pending_imports:
      options_arr = pending_import.getOptionsArr(include_keys=True)

      if len(options_arr) > 1:
        self.view.show_popup_menu(options_arr, self.onOptionSelected)
      else:
        self.onOptionSelected(len(options_arr) - 1)

  def onOptionSelected(self, index):
    for pending_import in self.pending_imports:
      if not pending_import.resolved:
        pending_import.resolved = True
        if index != -1:
          option_obj = pending_import.getOptionByIndex(index)

          # Make every path relative to view file
          if option_obj["key"] != "modules":
            option_obj["value"] = self.parsePath(
              path.normpath(
                path.relpath(
                  option_obj["value"],
                  self.view_dir_relpath
                )
              )
            )

          self.interpreter.onSearchResultChosen(
            pending_import.interpreted,
            option_obj['key'],
            option_obj['value'],
            mode=self.mode
          )
        break

    if False not in [ pending.resolved for pending in self.pending_imports ]:
      self.onPendingImportsResolved()

  def onPendingImportsResolved(self):
    for interpreted in self.interpreted_list:
      resolved_interpreted = self.interpreter.parseBeforeInsert(
        interpreted,
        self.view_imports,
        mode=self.mode
      )

      if resolved_interpreted not in self.imports_to_insert:
        self.imports_to_insert.append(resolved_interpreted)

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

  def parsePath(self, path):
    if path[:2] == "./" or path[:3] == "../":
      return path
    else:
      return "./" + path

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
    if path.isfile(path.join(self.project_path, SimpleImport.SETTINGS_FILE)):
      with open(path.join(self.project_path, SimpleImport.SETTINGS_FILE)) as raw_json:
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
          SimpleImport.log_error("Failed to load .simple-import.json at {0}".format(self.project_path))

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

    self.interpreter.setSettings(obj)

class ReplaceCommand(sublime_plugin.TextCommand):
  def run(self, edit, characters, start=0, end=False):
    if(end == False and end != 0):
      end = self.view.size()
    self.view.replace(edit,sublime.Region(start, end), characters)

class InsertAtCommand(sublime_plugin.TextCommand):
  def run(self, edit, characters, start=0):
    self.view.insert(edit, start, characters)

SimpleImport.loadInterpreters()
