import sublime, sublime_plugin, re

class Importation:
	def __init__(self, word):

		self.fromModule = False
		self.alternative = False

		word = word.strip().replace(" ", "")

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

		insertMode = args.get('insert')

		selections = self.view.sel();
		imports = ""
		begin = selections[0].begin()


		# if only one expression was selected
		shouldReplaceForName = selections[0] == selections[-1]
		uniqueImportObject = False

		for selection in selections:
			words = (self.view.substr(selection)).split(",")
			if len(words) > 1:
				shouldReplaceForName = False

			for word in words:

				if not word:
					continue

				importObject = Importation(word)
				imports += importObject.toString()

				# not the last one
				if word != words[-1] or insertMode:
					imports += "\n"

				if shouldReplaceForName:
					uniqueImportObject = importObject


			if(insertMode):
				self.view.insert(edit, 0, imports)
			else:
				self.view.run_command("replace", {"characters": imports, "start": selection.begin(), "end": selection.end()})
			imports = ""

		# If only one expression was selected it replaces the expression with the name of the importation
		if shouldReplaceForName and uniqueImportObject != False and insertMode:
			self.view.run_command("replace", {"characters": uniqueImportObject.name, "start": selections[0].begin(), "end": selections[0].end()})

		goTo = self.view.sel()[0].end()
		self.view.sel().clear()
		self.view.sel().add(sublime.Region(goTo))


