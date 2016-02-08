# Simple Import JS
A Simple Sublime Text Plugin that helps you to import your modules.


![example gif](https://raw.githubusercontent.com/vini175pa/simple-import-js/master/example.gif)

# Examples
NOTE! Currently this plugin does not search for files in the project. It 'just' converts expressions in js imports ( import or require).

`name[:module][:type]` is converted to `import name from 'module'`

#### name
This can be either a path, a name or the variable that will be defined for the module.

	React; ./stores/BaseStore` 

becomes...

	import React from 'react';
	import BaseStore from './stores/BaseStore';


#### module
(Optional) You can set the module to be imported. It can be a path or a simple module.

	ReactDOM:react-dom; Utils:../Path/to/utils.jsx

becomes...
	
	import ReactDOM from 'react-dom';
	import Utils from '../Path/to/utils.jsx';

#### type
(Optional) Sometimes you dont want to use ES6 import, so just add ':$' at the end and it will be converted to `require` instead of import.

	React:$; React-DOM:$

becomes...

	var React = require('react');
	var ReactDOM = require('react-dom');

## Import a method
If you put "::" between the name and the module, it will import a method or a propertie of it.

	ActonTypes::./constants/AppConstants
	ActonTypes::./constants/AppConstants:$
	
becomes...

	import {ActonTypes} from './constants/AppConstants';
	var ActionTypes = require('./constants/AppConstants').ActionTypes;
	

#### Multiple at once
You can import as many modules you want at once, just separate them with a semicolon.

	React;./Example.jsx;A::B

becomes...

	import React from 'react';
	import Example from './Example.jsx';
	import {A} from 'B';
	
	
# Installation
Just clone this repository in your packages folder and add the key bindings

 - Use `Ctrl+Shift+P` and find `Browse Packages`. Press ENTER and it will open the packages folder.
 - Clone this repository `git clone https://github.com/vini175pa/simple-import-js.git`
 - [Add the key bindings](#key-binding)
	
# Key Binding
Just add this in your **Preferences > Key Bindings - User**

	
	{ "keys": ["ctrl+alt+j"], "command": "import_es6"},
	{ "keys": ["ctrl+alt+i"], "command": "import_es6", "args": { "insert": true}}
	

# Notes
This project is just starting. I know it doesn't does much yet, but I hope it will become a bigger plugin in the near future. Feel free to contribute, to criticize the code lol. :)
