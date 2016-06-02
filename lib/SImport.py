class SImport:
  def __init__(self, interpreted, sSelection):
    self.interpreted = interpreted
    self.handler = interpreted.handler
    self.sSelection = sSelection
    self.statements = interpreted.interpreter.parseStatements(self.handler.getStatements(sSelection.expression, sSelection.context, interpreted.match))

  def __str__(self):
    return self.handler.getResultWithStatements(self.statements)
