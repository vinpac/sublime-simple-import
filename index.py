# If you detect any bug or run into some error, report so it can be fixed at https://github.com/vini175pa/simple-import-js

import sublime, sublime_plugin, re, os, json

IMPORT_ES6_REGEX = "import[\s]+(?P<isFromModule>\{)?[\s]*(?P<names>(([\s]*,[\s]*|[^\s\{\}\.])+))+[\s]*(?P<isFromModule2>\})?[\s]+from[\s]+(\'|\")(?P<module>.+)(\'|\")"

# Regex to ecounter an import or a require by its variable name
# double brackets are turned on one in str.format
ANY_IMPORT_BY_NAME_REGEX = "(import[\s]+\{{?[\s]*{name}[\s]*\}}?[\s]+from[\s]+(\'|\").+(\'|\")|((var[\s]+)?){name}[\s]*\=[\s]*require\([\s]*(\'|\").+(\'|\")[\s]*\)([\s]*\.[\s]*\w+)?)([\s]*;)?"

PENDING_STATUS = "pending"
RESOLVED_STATUS = "resolved"

DEFAULT_SETTINGS = {
	"paths" : {},
	"separator" : ";",
	"name_separator" : ":",
	"from_indicator" : "::",
	"excluded_directories" : [],
	"extensions" : [ "js" ],
	"remove_index_from_path": True,
	"search_indicator" : "@",
	"search_ignorecase_indicator" : "!",
	"settings_file"  : ".simple-import.json",
	"search_by_default" : True,
	"search_ignorecase_by_default" : True,
	"es6_by_default" : True
}

class ImportSelection:
	def __init__(self, region, index=0, importObjs=[]):
		self.region = region
		self.importObjs = importObjs
		self.index = index
		self.status = PENDING_STATUS

	def addImportObj(self, importObj):
		self.importObjs.append(importObj)

	def resolve(self):
		self.status = RESOLVED_STATUS

	def isPending(self):
		return self.status == PENDING_STATUS

	def areImportsPending(self):
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
		self.searchFlags = {
			"caseInsesitive": SimpleImportCommand.settings.get("search_ignorecase_by_default")
		}

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
		self.checkSearchForWord(name)

		# Remove some characters
		name = "".join([x for x in name if x not in ["!", "@", "*"]])

		if("/" in name):
			splited = name.split("/")
			name = splited[-1]
			if name == "index":
				name = splited[-2] or names

		if("-" in name):
			words = name.split("-")
			name = words[0]
			for word in words[1:]:
				name += word[0].upper() + word[1:]


		if("." in name):
			name = name.split(".")[0]

		return name

	def parseModule(self, module):
		self.checkSearchForWord(module)

		if(SimpleImportCommand.settings.get("search_indicator") in module):
			module = module.replace(SimpleImportCommand.settings.get("search_indicator"), "")

		if("/" not in module):
			module = module.lower()

		return module

	def checkSearchForWord(self, word):
		indicator = word[:2]
		remove_len = 0
		settings = SimpleImportCommand.settings
		search = settings.get("search_by_default")

		if settings.get("search_indicator") in indicator:
			remove_len += len(settings.get("search_indicator"))
			search = not settings.get("search_by_default")



		if settings.get("search_ignorecase_indicator") in indicator:
			self.searchFlags["caseInsesitive"] = not settings.get("search_ignorecase_by_default")
			remove_len += len(settings.get("search_ignorecase_indicator"))
			search = search and settings.get("search_by_default")


		if search:
			self.searchForFiles = True
			self.searchFor = word[remove_len:]

		return search


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
		es6_by_default = SimpleImportCommand.settings.get("es6_by_default")

		if es6_by_default if self.alternative else not es6_by_default :
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


class SimpleImportCommand(sublime_plugin.TextCommand):

	settings = {}

	def run(self, edit, **args):

		self.project_root = self.view.window().extract_variables()['folder']
		self.project_path_length = len(self.project_root)



		self.viewPath = "" if not self.view.file_name() else os.path.relpath(self.view.file_name(), self.project_root)
		self.viewRelativeDir = os.path.dirname(self.viewPath) if self.viewPath != "." else ""
		self.filename = os.path.basename(self.viewPath)

		self.loadSettings()

		self.insertMode = args.get('insert')

		self.pendingImports = []
		self.selectionsObjs = []

		selections = self.view.sel();

		# if only one expression was selected
		self.uniqueImport = selections[0] == selections[-1]

		selectionIndex = 0

		for selection in selections:

			self.imports = ""
			selectionObj =  ImportSelection(selection, selectionIndex)

			self.selectionsObjs.append(selectionObj)

			words = re.split("{0}|\n".format(MODULE_SEPARATOR), self.view.substr(selection))

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
					searchResults = self.searchFiles(importObj.searchFor, **importObj.searchFlags)

					importObj.setResults(searchResults)
					if len(searchResults) > 1:
						self.pendingImports.append(importObj)
						self.view.show_popup_menu(searchResults, self.handleClickItem)
						continue
					elif len(searchResults) == 1:
						importObj.setModule(self.parseModulePath(searchResults[0]), True)

				self.handleImportObj(importObj, selectionObj)

			selectionIndex += 1
			self.resolveSelection(selectionObj)


	def loadSettings(self):

		settings = SimpleImportCommand.settings
		settings.update(DEFAULT_SETTINGS)

		sublime_settings = self.view.settings().get("simple-import") or False

		if sublime_settings:
			settings.update(sublime_settings)

		if os.path.isfile(os.path.join(self.project_root, settings["settings_file"])):
			with open(os.path.join(self.project_root, settings["settings_file"])) as data_file:
				try:
					data = json.load(data_file)
				except ValueError:
					print("SIMPLE-IMPORT ERROR :: Error trying to load {0}".format(settings["settings_file"]))
					data = {}

				pData = False
				if data["paths"]:
					for key, value in data["paths"].items():
						pData = self.resolveSettingsForPath(key, value)
						if pData:
							settings.update(pData)
							break

				if not pData:
					settings.update(data)

		return settings

	def resolveSettingsForPath(self, key, value, ):
		paths = None
		settings = None
		if isinstance(value, dict):
			settings = value
			if isinstance(key, list):
				paths = key
			else:
				paths = [ key ]
		elif isinstance(value, list):
			return self.resolveSettingsForPath(value[:-1], value[-1])
		else:
			return False

		return settings if re.search("^({0})".format("|".join(paths)), self.viewPath) else False



	def resolveSelection(self, selectionObj):
		if selectionObj.areImportsPending():
			return

		if self.imports.strip() != "":
			if(self.insertMode):
				self.view.run_command("insert_at", {"characters": self.imports})
			else:
				self.view.run_command("replace", {"characters": self.imports, "start": selectionObj.region.begin(), "end": selectionObj.region.end()})

		selectionObj.resolve()

		allSelectionsResolved = True
		for  x in self.selectionsObjs:
			if x.isPending():
				allSelectionsResolved = False

		if allSelectionsResolved:
			self.onDone()

	def onDone(self):
		goTo = self.view.sel()[-1].end()
		self.view.sel().clear()
		self.view.sel().add(sublime.Region(goTo))

	def handleClickItem(self, index):
		importObj = self.pendingImports.pop(0)

		if(index == -1):
			importObj.selectionObj.importObjs.remove(importObj)
			self.resolveSelection(importObj.selectionObj)
			return


		importObj.setModule(self.parseModulePath(importObj.searchResults[index]), True)

		self.handleImportObj(importObj, importObj.selectionObj)
		self.resolveSelection(importObj.selectionObj)

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


	def findImportationByName(self, word):
		return self.view.find(r"{0}".format(ANY_IMPORT_BY_NAME_REGEX.format(name=word)), 0);

	def isAlreadyImported(self, word):
		if isinstance(word, sublime.Region):
			region = word
		else:
			region = self.findImportationByName(word)
		return region.begin() != -1 or region.end() != -1

	def searchFiles(self, search, includeViewFile=False, caseInsesitive=False):

		results = []
		searchWithFolders = False

		settings = SimpleImportCommand.settings

		_search = search.replace("/", "\/");
		_search = _search.replace("*", "");
		regex = "({0}{1}|{0}\/index){2}$".format(_search, "(.)*" if search[-1] == "*" else "", "\.({0})".format("|".join(settings.get("extensions"))));

		for dirpath, dirnames, filenames in os.walk(self.project_root, topdown=True):

			crpath = dirpath[self.project_path_length + 1:] + "/" if dirpath != self.project_root else ""

			dirnames[:] = [dirname for dirname in dirnames if ( crpath + dirname  ) not in settings.get("excluded_directories")]


			for filename in filenames:
				if includeViewFile or ( not includeViewFile and crpath + filename != self.viewPath):
					if re.search(regex, crpath + filename,  re.IGNORECASE if caseInsesitive else False):
						results.append(crpath + filename)

		return results

	def parseModulePath(self, path):

		splited = path.split("/")
		filename = path if "/" not in path else splited[-1]

		if "." in filename:
			extension = filename.split(".")[-1]

			if(extension in SimpleImportCommand.settings.get("extensions")):
				path = path[: (len(extension) + 1) * -1 ]

		if "/" in path and SimpleImportCommand.settings.get("remove_index_from_path") and splited[0].strip() != "" and path.endswith("index"):
			path = path[:-6]

		return os.path.relpath(path, self.viewRelativeDir)









