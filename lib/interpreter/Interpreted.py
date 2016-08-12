class Interpreted:
  IT_INSERT = "INSERT"
  IT_INSERT_AFTER = "INSERT_AFTER"
  IT_INSERT_BEFORE = "INSERT_BEFORE"
  IT_REPLACE = "REPLACE"
  IT_REPLACE_IMPORT = "REPLACE_IMPORT"

  def __init__(self, interpreter, statements, itype, simport):
    self.interpreter = interpreter
    self.simport = simport
    self.itype = itype
    self.statements = statements
    self.insert_type = Interpreted.IT_REPLACE

    # Fires onInterprete
    self.interpreter.onInterprete(self)

  def __str__(self):
    return self.interpreter.stringifyStatements(self.statements, itype=self.itype, insert_type=self.insert_type)
