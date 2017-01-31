from ..utils import flattenObjectToList

class PendingImport:

  keyTextMap = {
    "files": "Import: '{value}'",
    "modules": "Import Module: '{value}'",
    "exports": "Import: '{value}' from {key}",
    "module_exports": "Import: '{value}' from {key}",
    "module_files": "Import: '{value}'",
    "extra_files": "Import: '{value}'"
  }

  @staticmethod
  def parseQueryResultToList(queryResult, baseKey=None, include_keys=True):
    result = []

    for key in queryResult:
      if isinstance(queryResult[key], dict):
        result += PendingImport.parseQueryResultToList(
          queryResult[key],
          baseKey=key
        )
        continue

      type_key = baseKey if baseKey else key
      if include_keys and type_key in PendingImport.keyTextMap:
        text = PendingImport.keyTextMap[type_key]
      else:
        text = "{value}"

      result += [
        text.format(
          value=option,
          key=key
        ) for option in queryResult[key]
      ]

    return result

  def __init__(self, interpreted, options):
    self.interpreted = interpreted
    self.resolved = False
    self.options = self.interpreted.interpreter.parseOptions(
      interpreted,
      options
    )

  def getOptionsAsList(self, include_keys=True):
    return PendingImport.parseQueryResultToList(
      self.options,
      include_keys=include_keys
    )

  def getOptionByIndex(self, index):
    for key in self.options:
      if isinstance(self.options[key], dict):
        for module in self.options[key]:
          length = len(self.options[key][module])

          if index < length:
            return { "key": key, "value": module  }

          index -= length
      else:
        length = len(self.options[key])

        if index < length:
          return { "key": key, "value": self.options[key][index]  }
        index -= length
