Simple Import JS
===================

`Simple import` is a plugin for Sublime Text that imports your modules. Just select select the module you want to import and select "Simple Import: insert imports". You can import as many modules you want at once.

![Example image](https://raw.githubusercontent.com/vini175pa/simple-import-js/master/example.gif)



----------

Syntax
-------------

`[![@]]Name[:Module][:$]`

This is the syntax. Simple Import offers you some to import a module, like, where should it be searched, the searching um be case insensitive or not, and more. But wait, isn't this plugin SIMPLE? Yes, it its. Let's have a look.

**Name** is the variable name that will be used

**Module** ... common? Have a guess!

'**:**' separates the parts.

**@** Indicates if this should be searched or not. This is **True** by default

**!** Indicates if the search will be case sensitive or not. **True** by default

**$** Indicates if this is a ES6 Syntax import or not. If you add this, you will have `const Name = require("Module")`

 **Important - **  Double Separators between the Name and the Module make it an "import of property "

	ActionTypes::AppConstants`  = `import {ActionTypes} from 'AppConstants'
	ActionTypes::AppConstants:$`  = `const ActionTypes = require('AppConstants').ActionTypes

Every indicator or default setting can be defined in your project and in your sublime settings. Look at  [Configurations](#configurations) (optional)

Let's say you want to import `React`. Just add `React`, use the simple-import and BAM! `import React from react;` will be added at the top of your file. But what if you wanted set another variable instead of React? Use `NameYouWant:react` and it's gonna work: `import NameYouWant 'react'`

Lets say you have something like this:

	src/
		components/
			Login/
				index.jsx
			Register/
				index.jsx
			Home/
				index.js
		elements/
			input.jsx

If you try to import `index`, a dropdown will be open and show you the options. But, if you want to import an specific file, simply import `Login/index` and it's going to work.

Searching accepts some flags. Examples: `components/*/index`, `components/*/i*`, have fun!

----------

Configurations
-------------

To configurate Simple Import you can do 2 this. You can create a file on the root of your project called `.simple-import.json`. **IMPORTANT** This is a json file.

Example:

	{
		"excluded_directories" : [ ... ],
		...
	}


You can set `"simple-import" : { <here comes the settings> }` at your sublime settings to. ( **Preferences > Settings - User** )


## Options

**excluded_directories**  (Array) :   Directories that wont be matched. Example: `["node_modules", ".git"]`

**extensions**  (Array) :   Extensions to be matched on search and will be removed from file on import . Don't add "." (dot). **Default** `[ "js" ]`

**separator** (String) : The separator between imports. **Default** `;`

**name_separator** (String) : The separator. **Default** `:`

**from_indicator** (String) : Indicator that this is a "import of property". **Default** `::`

**remove_index_from_path** (Boolean): Indicates whether it should remove an `index` file from a path or not. Example `../Login/index` is modified to `../Login`. **Default** True

**search_indicator** (String): Indicator that it should search for a file or not. **Default** `@`

**search_ignorecase_indicator** (String) : Indicator that the search will be case sensitive or not.  **Default** `!`

**settings_file** (String) :  The path of the settings file for Simple Import. **Default** `.simple-import`

**search_by_default** (Boolean): Indicates if by default an import should do a search. The Search Indicator (`@`) makes the import do the opposite of the default. **Default** `True`

**search_ignorecase_by_default** :  (Boolean): Indicates if by default an import should do a search case insensitive ( ignore the cases) . The Ignore Case Indicator (`!`) makes the import do the opposite of the default. **Default** `True`

**es6_by_default** :  (Boolean): Indicates if by default an import should be an `import` or a `require`.  A `$` at the end of an import makes it do the opposite of the default. **Default** `True`


## Different settings for each path

If you want to use different settings for specific folders or files you can! In your `.simple-import.json` set only `paths`. Let's see an example:

	{
		"paths": {

			"nodejs" : [ "sockets.js",  "app.js", "routes", "passport", "models", "lib",
				{
					"es6_by_default": false,
					"excluded_directories": [ "react", "node_modules", ".git", "src" ]
				}
			],

			"react/components" : {
				"extensions": ["js", "jsx"]
			}

		}
	}

It only works on your `.simple-import.json` and won't work on sublime settings.


Installation
-------------

Just clone this repository in your packages folder and add the key bindings.

 - Open the Command Palette and find `Browse Packages`.  Select it and the packages folder will open.
 - Clone this repository in this folder
	 - On Terminal, clone this repository: `git clone https://github.com/vini175pa/simple-import-js.git`
	 - or Download this repository as `rar` and put the content inside the packages folder
 - [Add the key bindings](#key-binding) (optional)

# Key Binding
Just add this in your **Preferences > Key Bindings - User**

	{ "keys": ["ctrl+alt+j"], "command": "simple_import"},
	{ "keys": ["ctrl+alt+i"], "command": "simple_import", "args": { "insert": true}},
	{ "keys": ["ctrl+alt+u"], "command": "simple_import", "args": { "resolve": true}}


Contributing
-------------
Just be nice. Any name you don't agree with, bugs or suggestions, [create an Issue](https://github.com/vini175pa/simple-import-js/issues)! This helps a lot!

... And have in your mind that i'm not a python expert. This is my first module with python, actually.
