import sys, os.path, imp, sublime, sublime_plugin
# =======
# reload plugin files on change
if 'plugin_helpers.reloader' in sys.modules:
  imp.reload(sys.modules['plugin_helpers.reloader'])
  import plugin_helpers.reloader

class ReloadPlugin(sublime_plugin.EventListener):
  PACKAGE_NAME = 'TestRSpec'
  PLUGIN_RELOAD_TIME_MS = 200
  PLUGIN_PYTHON_FILE = os.path.join(PACKAGE_NAME, "test_rspec.py")

  def on_post_save(self, view):
    file_name = view.file_name()
    if not ReloadPlugin.PACKAGE_NAME in file_name: return
    if ReloadPlugin.PLUGIN_PYTHON_FILE in file_name: return

    original_file_name = view.file_name()
    plugin_python_file = os.path.join(sublime.packages_path(), ReloadPlugin.PLUGIN_PYTHON_FILE)
    if not os.path.isfile(plugin_python_file): return

    def _open_original_file():
      view.window().open_file(original_file_name)

    plugin_view = view.window().open_file(plugin_python_file)
    print("save", plugin_view.file_name())
    plugin_view.run_command("save")
    sublime.set_timeout_async(_open_original_file, self.PLUGIN_RELOAD_TIME_MS)
