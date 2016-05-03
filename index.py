import sublime, sublime_plugin, re, json
from os import path

class SImport:
  def __init__(self, handler, expression, context, sSelection):
    self.handler = handler
    self.expression = expression
    self.context = context
    self.sSelection = sSelection
    self.values = handler.values(expression, context)

  def __str__():
    return self.string.format(self.variable, self.module)

class Interpreter:

  def __init__(self, obj):
    self.syntax = obj["syntax"]
    self.handlers = self.parseHandlers(obj["handlers"])

  def parseHandlers(self, _handlers):
    handlers = []
    for key in _handlers:
      handlers.append( Interpreter.Handler.fromDict( _handlers[key] ) )
      if( "default" in _handlers[key] and _handlers[key]["default"] == True):
        self.defaultHandler = handlers[-1]

    if not self.defaultHandler and len(handlers):
      self.defaultHandler = handlers[1]

    return handlers

  def getHandlerFor(self, expression, context):
    for handler in self.handlers:
      if handler.test(expression, context):
        return handler

    return self.defaultHandler

  def resolve(self, expression, context, sSelection):
    return SImport(self.getHandlerFor(expression, context), expression, context, sSelection)

  class Handler:

    @staticmethod
    def fromDict(obj):
      handler = None
      try:
        handler = Interpreter.Handler(obj["match"], obj["result"])
      except KeyError:
        print("Error creating Handler from dict")
      return handler

    def __init__(self, matchers, result, default=False):
      self.matchers = [ Interpreter.Matcher(expression) for expression in matchers ]
      self.result = result.strip()

    def getMatcherFor(self, expression, context):
      for matcher in self.matchers:
        if matcher.match(context):
          return matcher

    def test(self, expression, context):
      return not not self.getMatcherFor(expression, context)

    def values(self, expression, context):
      matcher = self.getMatcherFor(expression, context)
      if matcher:
        return matcher.match(context).groupdict()

    def resolve(values):
      return self.result.replace(**values)

  class Matcher:

    @staticmethod
    def generateRegex(expression):
      regex = expression
      keys = re.findall(r"\{\w+\}", expression)
      for key in keys:
        regex = regex.replace(key, "(?P<" + key[1:-1] + ">[^\s]+)")
      regex = regex.replace(" ", "\s+")
      return regex

    def __init__(self, expression):
      self.expression = expression
      self.regex_expression = Interpreter.Matcher.generateRegex(expression)

    def match(self, string):
      return re.search(re.compile(self.regex_expression + "$"), string)

    def resolve(self, string):
      match = self.match(string)
      if match:
        return math.groupdict()

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

class SimpleImport():
  interpreters = {}

  @staticmethod
  def loadInterpreters():
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "interpreters.json")) as data_file:
      try:
        interpreters = json.load(data_file)
      except ValueError:
        print("SIMPLE-IMPORT ERROR :: Error trying to load {0} on project root.".format("interpreters.json"))
        interpreters = {}

    for key in interpreters:
      SimpleImport.interpreters[ interpreters[key]["syntax"] ] = Interpreter(interpreters[key])

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
      sSelection = SSelection( region, context, selection_index )

      expression = self.view.substr(region)
      context_content = self.view.substr(context)

      # sImport = SImport(expression, context_content, sSelection)
      # sImport.resolve(self.interpreter)
      # print(sImport.__str__())

      sImport = self.interpreter.resolve(expression, context_content, sSelection)
      print(sImport.values)

      #self.view.run_command("replace", {"characters": result.__str__(), "start": result.region.begin(), "end": result.region.end()})


  def handle(self):
    print("handle")

  def getInterpreter(self, syntax):
    for key in SimpleImport.interpreters:
      if re.search(r"^{0}".format(key), syntax, re.IGNORECASE):
        return SimpleImport.interpreters[key]
    return None


class ReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit, characters, start=0, end=False):
      if(end == False):
        end = self.view.size()
      self.view.replace(edit,sublime.Region(start, end), characters)

SimpleImport.loadInterpreters()
