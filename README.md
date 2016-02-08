# Sublime Import JS
A Sublime Text Plugin that helps you to import your modules.

![example gif](https://raw.github.com/vini175pa/sublime-import-js/master/example.gif)

# Examples
NOTE! Currently this plugin does not search for files in the project. It 'just' converts expressions in js imports ( import or require).

`name[:module][:type]` is converted to `import name from 'module'`

#### name
This can be either a path, a name or the variable that will be defined for the module.

`React`  ->  `import React from 'react'`

`./stores/BaseStore`  ->  `import BaseStore from './stores/BaseStore'`

#### module
(Optional) You can set the module to be imported. It can be a path or a simple module.

`ReactDOM:react-dom` -> `import ReactDOM from 'react-dom'`

`Utils:../Path/to/utils.jsx` -> `import Utils from '../Path/to/utils.jsx'`

#### type
(Optional) Sometimes you dont want to use ES6 import, so just add ':$' at the end and it will be converted to `require` instead of import.

  `ReactDOM:react-dom:$` -> `var ReactDOM = require('react-dom');`

#### Import method
If you put "::" between the name and the module, it will import a method or a propertie of it.

`ActonTypes::./constants/AppConstants` -> `import {ActonTypes} from './constants/AppConstants'`

`ActonTypes::./constants/AppConstants:$` -> `var ActionTypes = require('./constants/AppConstants').ActionTypes`

#### Multiple at once
	You can import as many modules you want at once, just separate them with a semicolon.

	`React;./Example.jsx;A::B`
	becomes...
	`import React from 'react';
	import Example from './Example.jsx';
	import {A} from 'B';`

# Notes
This project is just starting. I know it doesn't does much yet, but I hope it will become a bigger plugin in the near future. Feel free to contribute, to criticize the code lol. :)
