# If you detect any bug or run into some error, report so it can be fixed at https://github.com/vini175pa/simple-import-js

import sublime, sublime_plugin, re, os, json

IMPORT_ES6_REGEX = "import[\s]+(?P<isFromModule>\{)?[\s]*(?P<names>(([\s]*,[\s]*|[^\s\{\}\.])+))+[\s]*(?P<isFromModule2>\})?[\s]+from[\s]+(\'|\")(?P<module>.+)(\'|\")"

# Regex to ecounter an import or a require by its variable name
# double brackets are turned on one in str.format
ANY_IMPORT_BY_NAME_REGEX = "(import[\s]+\{{?[\s]*{name}[\s]*\}}?[\s]+from[\s]+(\'|\").+(\'|\")|((var[\s]+)?){name}[\s]*\=[\s]*require\([\s]*(\'|\").+(\'|\")[\s]*\)([\s]*\.[\s]*\w+)?)([\s]*;)?"

SEARCH_IGNORECASE_INDICATOR = "!"
MODULE_SEPARATOR = ";"
NAME_MODULE_SEPARATOR = ":"
IMPORT_FROM_SEPARATOR = "::"
SEARCH_INDICATOR = "@"

PENDING_STATUS = "pending"
RESOLVED_STATUS = "resolved"

DEFAULT_SETTINGS_FILE = ".simple-import"

REMOVE_INDEX_FROM_PATH = True

class Settings:
	def __init__(self, obj={}):
		self.obj = {}

	def set(self, key, value):
		self.obj[key] = value

	def get(self, key):
		return self.obj[key]

	def update(self, obj):
		self.obj.update(obj)

	def setObj(self, obj):
		self.obj = obj

mSettings = Settings()

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
		self.searchFlags = {}

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
		if(mSettings.get("search_indicator") in name):
			self.checkSearchForWord(name)
			name = name.replace(mSettings.get("search_indicator"), "")

		if("*" in name):
			name = name.replace("*", "")

		if("!" in name):
			name = name.replace("!", "")

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

	def parseModule(self, module):
		if(mSettings.get("search_indicator") in module):
			self.checkSearchForWord(module)
			module = module.replace(mSettings.get("search_indicator"), "")

		if("/" not in module):
			module = module.lower()

		return module

	def checkSearchForWord(self, word):
		if word[:2] == mSettings.get("search_ignorecase_indicator") + mSettings.get("search_indicator"):
			self.searchFlags["caseInsesitive"] = True
			self.searchFor = word[len(  mSettings.get("search_ignorecase_indicator") + mSettings.get("search_indicator") ):]
		elif word[0] != mSettings.get("search_indicator"):
			return False
		else:
			self.searchFor = word[len(mSettings.get("search_indicator")):]

		self.searchForFiles = True

		return True


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

		self.loadSettings()

		self.viewPath = "" if not self.view.file_name() else os.path.relpath(self.view.file_name(), self.project_root)
		self.viewRelativeDir = os.path.dirname(self.viewPath) if self.viewPath != "." else ""
		self.filename = os.path.basename(self.viewPath)

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

		settings = {
			"separator" : MODULE_SEPARATOR,
			"name_separator" : NAME_MODULE_SEPARATOR,
			"from_indicator" : IMPORT_FROM_SEPARATOR,
			"excluded_directories" : [],
			"excluded_extensions" : [],
			"remove_index_from_path": True,
			"search_indicator" : SEARCH_INDICATOR,
			"search_ignorecase_indicator" : SEARCH_IGNORECASE_INDICATOR,
			"settings_file"  : DEFAULT_SETTINGS_FILE
		}

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
				settings.update(data)

		mSettings.setObj(settings)

		return mSettings

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
		print(mSettings.get("excluded_directories"))
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

		for dirpath, dirnames, filenames in os.walk(self.project_root, topdown=True):

			crpath = dirpath[self.project_path_length + 1:] + "/" if dirpath != self.project_root else ""

			dirnames[:] = [dirname for dirname in dirnames if ( crpath + dirname  ) not in mSettings.get("excluded_directories")]


			_crpath = crpath if searchWithFolders else ""

			for filename in filenames:
				if includeViewFile or ( not includeViewFile and crpath + filename != self.viewPath):
					if re.search(regex, _crpath + filename,  re.IGNORECASE if caseInsesitive else False):
						results.append(crpath + filename)

		return results

	def parseModulePath(self, path):

		splited = path.split("/")
		filename = path if "/" not in path else splited[-1]

		if "." in filename:
			extension = filename.split(".")[-1]

			if(extension in mSettings.get("excluded_extensions")):
				path = path[: (len(extension) + 1) * -1 ]


		if "/" in path and mSettings.get("remove_index_from_path") and splited[0].strip() != "" and path[-5:] == "index":
			path = path[:-6]

		return os.path.relpath(path, self.viewRelativeDir)









