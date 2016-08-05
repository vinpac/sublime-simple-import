import re

def joinStr(value, regex=None):
  words = re.split(regex if regex else r"_|-|\/|-|\.", value)
  value = words[0]
  for word in words[1:]:
    value += word[0].upper() + word[1:]
  return value

def ucfirst(string):
  return string[0].upper() + string[1:]
