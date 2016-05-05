import sublime, sublime_plugin, re, json
from os import path

class SImport:
  def __init__(self, interpreted, sSelection):
    self.interpreted = interpreted
    self.handler = interpreted.handler
    self.sSelection = sSelection
    self.statements = self.handler.getStatements(sSelection.expression, sSelection.context, interpreted.match)

  def __str__(self):
    return self.handler.getResultWithStatements(self.statements)

# =============================================================================================

class Interpreter:

  def __init__(self, obj):
    self.syntax = obj["syntax"]
    self.createHandlers(obj["handlers"])
    self.createKeys(obj["keys"] if "keys" in obj else [])

  def createKeys(self, keys):
    self.keys_names = []
    self.keys = []
    for name in keys:
      self.keys_names.append(name)
      self.keys.append(Interpreter.Key(name, keys[name]))

  def createHandlers(self, handlers):
    self.handlers = []
    for key in handlers:
      obj = handlers[key]
      try:
        handler = Interpreter.Handler(obj["match"], obj["result"])
      except KeyError:
        print("Error creating Handler from dict")

      self.handlers.append( handler )

      if( "default" in handlers[key] and handlers[key]["default"] == True):
        self.defaultHandler = self.handlers[-1]

    if not self.defaultHandler and len(handlers):
      self.defaultHandler = self.handlers[1]

  def getKeys():
    return self.keys

  def getKeysNames():
    return self.keys_names

  def interprete(self, expression, context):
    for handler in self.handlers:
      match = handler.match(expression, context)
      if match:
        return Interpreter.Interpreted(self, handler, match)

    return Interpreter.Interpreted(self, handler)

  def resolve(self, sSelection):
    return SImport(self.interprete(sSelection.expression, sSelection.context), sSelection)

  # ===================================================================
  
  class Interpreted:
    def __init__(self, interpreter, handler, match=None):
      self.interpreter = interpreter
      self.handler = handler
      self.match = match

  # ===================================================================

  class Key:
    def __init__(self, name, params):
      self.name = name

  # ===================================================================

  class Handler:
      
    def __init__(self, matchers, result):
      self.matchers = [ Interpreter.Matcher(expression) for expression in matchers ]
      self.result = result.strip()

      arr = re.findall(r"\{\w+\}", self.result)
      self.keys = [ x[1:-1] for x in arr]

    def match(self, expression, context):
      for matcher in self.matchers:
        match = matcher.match(context)
        if match:
          return match

    def getStatements(self, expression, context, match=None):
      if not match:
        match = self.match(expression, context)

      if match:
        statements = match.groupdict()
        values = list(statements.values())
      else:
        statements = {}
        values = SimpleImport.expressionInContext(expression, context).split(":")

      keys = self.keys
      index = 0
      length = len(values)

      for key in keys:
        if not key in statements:
          statements[key] = values[index]
          index = min(index + 1, length - 1)

      print(statements)
      return statements
      
    def getResultWithStatements(self, statements):
      result = self.result
      for key in statements:
        result = result.replace("{"+key+"}", statements[key])
      return result

  # ===================================================================

  class Matcher:

    @staticmethod
    def generateRegex(expression):
      regex = expression
      keys = re.findall(r"\{\w+\}", expression)
      for key in keys:
        regex = regex.replace(key, "(?P<" + key[1:-1] + ">[^\s]+)")
      regex = regex.replace(" ", "\s+")
      
      return re.compile(regex + "$")

    def __init__(self, expression):
      self.expression = expression
      self.regex_expression = Interpreter.Matcher.generateRegex(expression)

    def match(self, string):
      return re.search(self.regex_expression, string)

    def getMatchGroup(self, string):
      match = self.match(string)
      if match:
        return math.groupdict()


# ===================================================================

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
  def expressionInContext(expression, context):
    match = re.search(r"[^\.;\s]*{0}".format(expression), context)
    if match:
      return match.group(0)
    return expression

  @staticmethod
  def loadInterpreters():
    with open(path.join(path.dirname(path.realpath(__file__)), "interpreters.json")) as data_file:
      try:
        interpreters = json.load(data_file)
      except ValueError:
        print("SIMPLE-IMPORT ERROR :: Error trying to load {0} on project root.".format("interpreters.json"))
        interpreters = {}

    for key in interpreters:
      SimpleImport.interpreters[ interpreters[key]["syntax"] ] = Interpreter(interpreters[key])


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
