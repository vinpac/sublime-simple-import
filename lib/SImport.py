class SImport:
  def __init__(self, interpreted, sSelection):
    self.interpreted = interpreted
    self.handler = interpreted.handler
    self.statements = interpreted.interpreter.parseStatements(self.handler.getStatements(sSelection, interpreted.match))

  def __str__(self):
    return self.handler.getResultWithStatements(self.statements)
