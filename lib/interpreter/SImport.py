import re
from sublime import Region
class SImport:
  @staticmethod
  def getExpressionInContext(expression, context):
    match = re.search(r"[^\{{\}}\(\)\<\>\.;\s]*{0}$".format(expression), context)

    if match:
      return match.group(0)
    return expression

  def __init__(self, expression, context, region, context_region):
    self.expression = self.getExpressionInContext(expression, context)
    self.region = Region(region.end() - len(self.expression), region.end())
    self.context = context
    self.context_region = context_region
