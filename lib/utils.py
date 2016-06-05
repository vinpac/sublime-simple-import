import re
def expressionInContext(expression, context):
  match = re.search(r"[^\.;\s]*{0}".format(expression), context)
  if match:
    return match.group(0)
  return expression

def joinStr(value, regex=None):
  words = re.split(regex if regex else r"_|-|\/|-|\.", value)
  value = words[0]
  for word in words[1:]:
    value += word[0].upper() + word[1:]
  return value

def ucfirst(string):
  return string[0].upper() + string[1:]
