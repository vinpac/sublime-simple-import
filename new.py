import os, re, json

class SImport:
  def __init__(self, parser, expression, context=False):
    self.parser = parser
    self.expression = expression
    self.context = context

  def __str__(self):
    return "asdad"

class Interpreter:

  def __init__(self, obj):
    self.handlers = self.parseHandlers(obj["imports"])

  def parseHandlers(self, _handlers):
    handlers = []
    for key in _handlers:
      handlers.append( Interpreter.Handler.fromDict( key, _handlers[key] ) )
      if( handlers[-1].default ):
        self.default = handlers[-1]

    if not self.default and len(handlers):
      self.default = handlers[1]

    return handlers

  def handle(self, expression, context):

    for handler in self.handlers:
      result = handler.handle(expression, context)
      if result:
        return result

    if not result:
      return self.default.resolve(expression.strip(), expression.strip())


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
        if re.search(re.compile(test.format(variable=expression, expression=expression, module=expression) + "$"), context):
          result = test
      return result

    def handle(self, expression, context):
      matched = self.test(expression, context)
      if not matched:
        return matched

      if "{variable}" in matched:
        return self.resolve(expression, expression)

    def resolve(self, variable, module):
      return self.result.format(variable=variable, module=module)


    def parseTest(self, test):
      test = test.strip()
      # test = test.replace("{variable}", "(?P<variable>.+)")
      # test = test.replace("{module}", "(?P<module>.+)")
      # test = test.replace("{expression}", "(?P<expression>[^\s]+)")
      # test = test.replace(" ", "\s+")
      if "{module}" in test:
        test = test.replace("{variable}", "(.+)")

      #test = test.replace("{module}", "{1}")
      #test = test.replace("{expression}", "(?P<expression>[^\s]+)")
      test = test.replace(" ", "\s+")
      return test

    def parseResult(self, result):
      return result.strip()

class SimpleImport:

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

  def run(self):
    current_file_extesion = "js"

    try:
      self.interpreter = SimpleImport.interpreters[current_file_extesion]
    except KeyError:
      print("Simple import does not support '.{0}' files yet".format(current_file_extesion))
      return


    print( self.interpreter.handle("Post", "import Post").__str__() )
    print( self.interpreter.handle("Post", " Post").__str__() )
    print( self.interpreter.handle("Avatar", "import Post from Avatar").__str__() )

#SimpleImport.loadParsers()
#s = SimpleImport()
#s.run()