import sublime, sublime_plugin, re, os

IMPORT_ES6_REGEX = "import[\s]+(?P<isFromModule>\{)?[\s]*(?P<names>(([\s]*,[\s]*|[^\s\{\}\.])+))+[\s]*(?P<isFromModule2>\})?[\s]+from[\s]+(\'|\")(?P<module>.+)(\'|\")"

# Regex to ecounter an import or a require by its variable name
# double brackets are turned on one in str.format
ANY_IMPORT_BY_NAME_REGEX = "(import[\s]+\{{?[\s]*{name}[\s]*\}}?[\s]+from[\s]+(\'|\").+(\'|\")|((var[\s]+)?){name}[\s]*\=[\s]*require\([\s]*(\'|\").+(\'|\")[\s]*\)([\s]*\.[\s]*\w+)?)([\s]*;)?"


MODULE_SEPARATOR = ";"
NAME_MODULE_SEPARATOR = ":"
IMPORT_FROM_SEPARATOR = "::"

excluded_directories = ["./.git", "node_modules"]
excluded_directories = [os.path.normpath(path) for path in excluded_directories if (path != "." or path != "./")]

excluded_extensions = ["js", "jsx"]

PENDING_STATUS = "pending"
RESOLVED_STATUS = "resolved"

REMOVE_INDEX_FROM_PATH = True

class ImportSelection:
	def __init__(self, region, index=0, importObjs=[]):
		self.region = region
		self.importObjs = importObjs
		self.index = index

	def addImportObj(self, importObj):
		self.importObjs.append(importObj)

	def isPending(self):
		isPending = False
		for x in self.importObjs:
			if x.isPending():
				isPending = True
				break

		return isPending

class Importation:

	@staticmethod
	def isImportWord(word):
		match = re.match(r'{0}'.format(IMPORT_ES6_REGEX), word.strip())
		return match

	def __init__(self, word, selectionObj):

		self.status = PENDING_STATUS
		self.searchResults = []
		self.selectionObj = selectionObj
		self.fromModule = False
		self.alternative = False
		self.searchForFiles = False

		word = word.strip()

		isImport = Importation.isImportWord(word)
		if isImport:
			isImport = isImport.groupdict()
			self.name = self.parseName(isImport["names"])
			self.module = isImport["module"]
			self.fromModule = isImport["isFromModule"]
			self.alternative = word.split(":")[-1] == "$"
			return
		else:
			word = word.replace(" ", "")

		self.word = word


		if ":" in word:

			if "::" in word:
				word = re.split("::|:", word)
				self.fromModule = True
			else:
				word = word.split(":")


			if word[-1] == "$":
				self.alternative = True

			if not word[1] or word[1] == "$":
				word[1] = word[0]




			self.name = self.parseName(word[0])
			self.module = self.parseModule(word[1])

		else:
			self.name = self.parseName(word)
			self.module = self.parseModule(word)

	def isPending(self):
		return self.status == PENDING_STATUS

	def isResolved(self):
		return self.status == RESOLVED_STATUS

	def resolve(self):
		self.status = RESOLVED_STATUS

	def setResults(self, searchResults):
		self.searchResults = searchResults

	def parseName(self, name):
		if("@" in name):

			if name[0] == "@":
				self.searchForFiles = True
				self.searchFor = name[1:]

			name = name.replace("@", "")

		if("/" in name):
			name = name.split("/")[-1]

		if("-" in name):
			words = name.split("-")
			name = words[0]
			for word in words[1:]:
				name += word[0].upper() + word[1:]


		if("." in name):
			name = name.split(".")[0]

		return name

	def setModule(self, module, isPath=False):
		if(isPath):
			self.module = self.parsePath(module)
		else:
			self.module = module


	def parsePath(self, path):

		if path[:2] == "./" or path[:3] == "../":
			return path
		else:
			return "./" + path

	def parseModule(self, module):
		if("@" in module):
			if module[0] == "@":
				self.searchForFiles = True
				self.searchFor = module[1:]

			module = module.replace("@", "")

		if("/" not in module):
			module = module.lower()

		return module

	def getEs6Import(self):
		name = self.name
		if self.fromModule:
			name = "{" + self.name + "}"
		else:
			name = self.name

		return "import {0} from \"{1}\";".format(name, self.module);

	def getRequire(self):
		if self.fromModule:
			end = ".{0};".format(self.name)
		else:
			end = ";"

		return "var {0} = require(\"{1}\"){2}".format(self.name, self.module, end)

	def __str__(self):
		if(self.alternative):
			return self.getRequire()
		else:
			return self.getEs6Import()

class ReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit, characters, start=0, end=False):
      if(end == False):
        end = self.view.size()
      self.view.replace(edit,sublime.Region(start, end), characters)

class InsertAtCommand(sublime_plugin.TextCommand):
    def run(self, edit, characters, start=0):
      self.view.insert(edit, start, characters)


class ImportEs6Command(sublime_plugin.TextCommand):

	def run(self, edit, **args):

		self.project_root = self.view.window().extract_variables()['folder']
		self.project_path_length = len(self.project_root)

		self.pendingImports = []

		self.viewPath = "" if not self.view.file_name() else os.path.relpath(self.view.file_name(), self.project_root)
		self.viewRelativeDir = os.path.dirname(self.viewPath) if self.viewPath != "." else ""
		self.filename = os.path.basename(self.viewPath)

		self.insertMode = args.get('insert')

		selections = self.view.sel();
		self.selectionsPending = {}

		# if only one expression was selected
		self.uniqueImport = selections[0] == selections[-1]

		selectionIndex = 0;
		for selection in selections:

			self.imports = ""
			selectionObj =  ImportSelection(selection, selectionIndex)
			words = (self.view.substr(selection)).split(MODULE_SEPARATOR)

			if not words[-1]:
				words = words[:-1]

			if len(words) > 1:
				self.uniqueImport = False


			for word in words:

				if not word:
					continue

				word = word.strip()

				importObj = Importation(word, selectionObj)

				selectionObj.addImportObj(importObj)


				if importObj.searchForFiles:
					searchResults = self.searchFiles(importObj.searchFor)

					importObj.setResults(searchResults)
					if len(searchResults) > 1:
						self.pendingImports.append(importObj)
						self.view.show_popup_menu(searchResults, self.handleClickItem)
						continue
					elif len(searchResults) == 1:
						importObj.setModule(self.parseModulePath(searchResults[0]), True)

				self.handleImportObj(importObj, selectionObj)

			selectionIndex += 1
			self.resolve(selectionObj)

	def handleClickItem(self, index):
		importObj = self.pendingImports.pop(0)

		importObj.setModule(self.parseModulePath(importObj.searchResults[index]), True)

		self.handleImportObj(importObj, importObj.selectionObj)
		self.resolve(importObj.selectionObj)

	def handleImportObj(self, importObj, selectionObj):

		alreadyImportedObject = self.findImportationByName(importObj.name)
		alreadyImported = self.isAlreadyImported(alreadyImportedObject)

		importObj.resolve()

		region = selectionObj.region

		if alreadyImported:
			self.view.run_command("replace", {"characters": importObj.__str__(), "start": alreadyImportedObject.begin(), "end": alreadyImportedObject.end()})
		else:
			self.imports += importObj.__str__()

		if self.uniqueImport and (self.insertMode or alreadyImported):
			region = self.view.sel()[selectionObj.index]
			self.view.run_command("replace", {"characters": importObj.name, "start": self.view.sel()[selectionObj.index].begin(), "end": self.view.sel()[selectionObj.index].end()})

		if alreadyImported:
			return

		if self.imports != "":
			self.imports += "\n"

	def resolve(self, selectionObj):
		if selectionObj.isPending():
			return

		if self.imports.strip() != "":
			if(self.insertMode):
				self.view.run_command("insert_at", {"characters": self.imports})
			else:
				self.view.run_command("replace", {"characters": self.imports, "start": selectionObj.region.begin(), "end": selectionObj.region.end()})



	def findImportationByName(self, word):
		return self.view.find(r"{0}".format(ANY_IMPORT_BY_NAME_REGEX.format(name=word)), 0);

	def isAlreadyImported(self, word):
		if isinstance(word, sublime.Region):
			region = word
		else:
			region = self.findImportationByName(word)
		return region.begin() != -1 or region.end() != -1

	def searchFiles(self, search, includeView=False):

		results = []
		searchWithFolders = False

		if("/" in search):
			regex = search.replace("/", "\/")
			regex = regex.replace("*\/", "(.+\/)?")
			if regex[0] == "/":
				regex = "^" + regex

			if regex[-1] == "*":
				regex = regex[:-1] + ".*"
			else:
				regex += "(\.[^\.]*)?$"

			regex = r"{0}".format(regex)
			searchWithFolders = True

		else :
			regex = search.replace("*", ".*")
			regex = r"^{0}(\.[^\.]*)?$".format(regex)

		print(regex)

		print(searchWithFolders)



		for dirpath, dirnames, filenames in os.walk(self.project_root, topdown=True):

			crpath = dirpath[self.project_path_length + 1:] + "/" if dirpath != self.project_root else ""

			dirnames[:] = [dirname for dirname in dirnames if ( crpath + dirname  ) not in excluded_directories]

			results = results + [crpath + filename for filename in filenames if re.search(regex, (crpath if searchWithFolders else "") + filename) ]

		return results

	def parseModulePath(self, path):

		splited = path.split("/")
		filename = path if "/" not in path else splited[-1]

		if "." in filename:
			extension = filename.split(".")[-1]

			if(extension in excluded_extensions):
				path = path[: (len(extension) + 1) * -1 ]


		if "/" in path and REMOVE_INDEX_FROM_PATH and splited[0].strip() != "" and path[-5:] == "index":
			path = path[:-6]

		return path









