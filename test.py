import re

search = "Login/index"


regex = search.replace("*/", "(.+\/)?")

if regex[0] == "/":
	regex = "^" + regex

if regex[-1] == "*":
	regex = regex[:-1] + ".*"
else:
	regex += "(\.[^\.]*)?$"

regex = r"{0}".format(regex)

print(regex)
print(re.search(r"{0}".format(search), "views/Login/index"))