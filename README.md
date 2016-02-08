# Simple Import JS
A Simple Sublime Text Plugin that helps you to import your modules.


![example gif](https://raw.githubusercontent.com/vini175pa/simple-import-js/master/example.gif)

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

#### Double separator
If you put a double separator instead of one, it will import a propertie of the module.

`ActonTypes::./constants/AppConstants` -> `import {ActonTypes} from './constants/AppConstants'`

`ActonTypes::./constants/AppConstants:$` -> `var ActionTypes = require('./constants/AppConstants').ActionTypes`

# Notes
This project is just starting. I know it doesn't does much yet, but I hope it will become a bigger plugin in the near future. Feel free to contribute, to criticize the code lol. :)
