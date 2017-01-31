import re

def joinStr(value, regex=None):
  words = re.split(regex if regex else r"_|-|\/|-|\.", value)
  value = words[0]
  for word in words[1:]:
    value += word[0].upper() + word[1:]
  return value

def ucfirst(string):
  return string[0].upper() + string[1:]

def extract_suffix(suffixes, value):
  for suffix in suffixes:
    if value.endswith(suffix):
      return suffix
  return None

def extract_prefix(prefixes, value):
  for prefix in prefixes:
    if value.startswith(prefix):
      return prefix
  return None

def endswith(suffixes, value):
  return extract_suffix(suffixes, value) != None

def flattenObjectToList(obj):
  result = []
  for key in obj:
    if isinstance(obj, dict):
      result += flattenObjectToList(obj)
    result.append(obj[key])
  return result

