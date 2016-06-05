import re
from .Interpreter import Interpreter

class Matcher:

    @staticmethod
    def generateRegex(expression):
      regex = expression
      keys = re.findall(r"\{\w+\}", expression)
      for key in keys:
        regex = regex.replace(key, "(?P<" + key[1:-1] + ">[^\s]+)")
      regex = regex.replace(" ", "\s+")

      return re.compile(regex + "$")

    def __init__(self, regex):
      self.regex = regex

    def match(self, string):
      return re.search(self.regex, string)

    def getMatchGroup(self, string):
      match = self.match(string)
      if match:
        return math.groupdict()
