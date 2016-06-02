import re
def expressionInContext(expression, context):
  match = re.search(r"[^\.;\s]*{0}".format(expression), context)
  if match:
    return match.group(0)
  return expression
