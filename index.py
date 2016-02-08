import sublime, sublime_plugin, re

IMPORT_ES6_REGEX = "import[\s]+(?P<isFromModule>\{)?[\s]*(?P<names>(([\s]*,[\s]*|[^\s\{\}\.])+))+[\s]*(?P<isFromModule2>\})?[\s]+from[\s]+(\'|\")(?P<module>.+)(\'|\")"
ANY_IMPORT_BY_NAME_REGEX = "(import[\s]+{0}[\s]+from[\s]+(\'|\").+(\'|\")|(var[\s]+)?{0}[\s]*\=[\s]*require\([\s]*(\'|\").+(\'|\")[\s]*\)([\s]*\.[\s]*{0})?)[\s]*;?"
MODULE_SEPARATOR = ";"


class Importation:

	@staticmethod
	def isImportWord(word):
		match = re.match(r'{0}'.format(IMPORT_ES6_REGEX), word.strip())
		return match

	def __init__(self, word):

		self.fromModule = False
		self.alternative = False

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

	def parseName(self, name):
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

	def toString(self):
		if(self.alternative):
			return self.getRequire()
		else:
			return self.getEs6Import()

class ReplaceCommand(sublime_plugin.TextCommand):
    def run(self, edit, characters, start=0, end=False):
      if(end == False):
        end = self.view.size()
      self.view.replace(edit,sublime.Region(start, end), characters)

class ImportEs6Command(sublime_plugin.TextCommand):
	def run(self, edit, **args):


		#project_root = self.view.window().extract_variables()['folder']

		insertMode = args.get('insert')

		selections = self.view.sel();

		# if only one expression was selected
		uniqueImport = selections[0] == selections[-1]

		selectionIndex = 0;
		for selection in selections:

			imports = ""
			words = (self.view.substr(selection)).split(MODULE_SEPARATOR)

			if not words[-1]:
				words = words[:-1]

			if len(words) > 1:
				uniqueImport = False


			for word in words:

				if not word:
					continue

				importObject = Importation(word)

				alreadyImportedObject = self.findImportationByName(importObject.name)
				alreadyImported = self.isAlreadyImported(alreadyImportedObject)


				if alreadyImported:
					self.view.run_command("replace", {"characters": importObject.toString(), "start": alreadyImportedObject.begin(), "end": alreadyImportedObject.end()})
				else:
					imports += importObject.toString()

				if uniqueImport and (insertMode or alreadyImported):
					selection = self.view.sel()[selectionIndex]
					self.view.run_command("replace", {"characters": importObject.name, "start": selection.begin(), "end": selection.end()})

				if alreadyImported:
					continue

				if imports != "":
					imports += "\n"

			if imports.strip() != "":
				if(insertMode):
					self.view.insert(edit, 0, imports)
				else:
					self.view.run_command("replace", {"characters": imports, "start": selection.begin(), "end": selection.end()})
			selectionIndex += 1
			imports = ""

		goTo = self.view.sel()[0].end()
		self.view.sel().clear()
		self.view.sel().add(sublime.Region(goTo))



	def findImportationByName(self, word):
		return self.view.find(r"{0}".format(ANY_IMPORT_BY_NAME_REGEX.format(word)), 0);

	def isAlreadyImported(self, word):
		if isinstance(word, sublime.Region):
			region = word
		else:
			region = self.findImportationByName(word)
		return region.begin() != -1 or region.end() != -1



