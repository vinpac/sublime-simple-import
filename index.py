import os, re, json

class SImport:
  def __init__(self, expression, context, sSelection, variable=None, module=None, parser=None, region=None):
    self.expression = expression
    self.context = context
    self.sSelection = sSelection
    self.variable = variable
    self.module = module
    self.parser = parser
    self.parser = parser
    self.resolved = not not module

  def __str__():
    return self.string.format(self.variable, self.module)

class Interpreter:

  def __init__(self, obj):
    self.handlers = self.parseHandlers(obj["handlers"])

  def parseHandlers(self, _handlers):
    handlers = []
    for key in _handlers:
      handlers.append( Interpreter.Handler.fromDict( key, _handlers[key] ) )
      if( handlers[-1].default ):
        self.default = handlers[-1]

    if not self.default and len(handlers):
      self.default = handlers[1]

    return handlers

  def handle(self, sImport):
    for handler in self.handlers:
      result = handler.handle(sImport)
      if result:
        return result

    if not result:
      return self.default.resolve(sImport)

  class Handler:

    @staticmethod
    def fromDict(key, obj):
      handler = None
      try:
        default = obj["default"] == True
        handler = Interpreter.Handler(key, obj["tests"], obj["result"], default=default)
      except KeyError:
        try:
          handler = Interpreter.Handler(key, obj["tests"], obj["result"])
        except KeyError:
          print("Error creating Handler from dict")
      return handler

    def __init__(self, key, tests, result, default=False):
      self.key = key
      self.tests = [ self.parseTest(test) for test in tests ]
      self.result = self.parseResult(result)
      self.default = default

    def test(self, expression, context):
      result = None
      for test in self.tests:

        if "{module}" in test:
          test = test.replace("{variable}", "(.+)")

        if re.search(re.compile(test.format(variable=expression, expression=expression, module=expression) + "$"), context):
          result = test
      return result

    def handle(self, sImport):
      matched = self.test(sImport.expression, sImport.context)
      if not matched:
        return matched

      if "{variable}" in matched and "{module}" in matched:
        return self.resolve(sImport.expression, sImport.expression)
      else:
        return self.resolve(sImport.expression, sImport.expression)

    def resolve(self, variable, module):
      return SImport( self.result, variable, module )

    def parseTest(self, test):
      test = test.strip()
      # test = test.replace("{variable}", "(?P<variable>.+)")
      # test = test.replace("{module}", "(?P<module>.+)")
      # test = test.replace("{expression}", "(?P<expression>[^\s]+)")
      # test = test.replace(" ", "\s+")
      #if "{module}" in test:
      # test = test.replace("{variable}", "(.+)")

      #test = test.replace("{module}", "{1}")
      #test = test.replace("{expression}", "(?P<expression>[^\s]+)")
      test = test.replace(" ", "\s+")
      return test

    def parseResult(self, result):
      return result.strip()

# Stands for Simple Selection
class SSelection:
  def __init__(self, region, context, index=0):
    self.index = index
    self.sImports = []
    self.resolved = False

    # Regions
    self.region = region
    self.context = context


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

class SimpleImportCommand(sublime_plugin.TextCommand):

  interpreters = {}

  @staticmethod
  def loadParsers():
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "expressions.json")) as data_file:
      try:
        interpreters = json.load(data_file)
      except ValueError:
        print("SIMPLE-IMPORT ERROR :: Error trying to load {0} on project root.".format("expressions.json"))
        interpreters = {}

    for key in interpreters:
      interpreter = Interpreter(interpreters[key])
      for ext in interpreters[key]["extensions"]:
        SimpleImport.interpreters[ ext ] = interpreter

  def run(self, edit):
    current_file_extesion = "js"

    try:
      self.interpreter = SimpleImport.interpreters[current_file_extesion]
    except KeyError:
      print("Simple import does not support '.{0}' files yet".format(current_file_extesion))
      return

    selections = self.view.sel()
    selection_index = 0

    for selection in selections:
      region = self.view.word(selection)
      context = sublime.Region(self.view.line(selection).begin(), region.end())
      sSelection = SSelection( region, context, selection_index )

      expression = self.view.substr(region)
      content_context = self.view.substr(context)

      sImport = SImport( expression, content_context, sSelection)

      result = self.interpreter.handle(sImport)

      self.view.run_command("replace", {"characters": result.__str__(), "start": result.region.begin(), "end": result.region.end()})


  def handle(self):
    print("handle")

class ReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit, characters, start=0, end=False):
      if(end == False):
        end = self.view.size()
      self.view.replace(edit,sublime.Region(start, end), characters)

SimpleImport.loadParsers()