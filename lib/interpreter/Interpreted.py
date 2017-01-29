class Interpreted:
  IT_INSERT = "INSERT"
  IT_INSERT_AFTER = "INSERT_AFTER"
  IT_INSERT_BEFORE = "INSERT_BEFORE"
  IT_REPLACE = "REPLACE"
  IT_REPLACE_IMPORT = "REPLACE_IMPORT"

  def __init__(self, interpreter, statements, handler_name, simport):
    self.interpreter = interpreter
    self.simport = simport
    self.handler_name = handler_name
    self.statements = statements
    self.insert_type = Interpreted.IT_REPLACE
    self.removed = False

  def remove(self):
    self.removed = True

  def __str__(self):
    if self.removed:
      return ''
    return self.interpreter.stringifyStatements(self.statements, handler_name=self.handler_name, insert_type=self.insert_type)
