Simple Import v2.0.0-alpha
===================

`Simple import` is a plugin for Sublime Text that imports your modules. Currently it works with Javascript and Python. If you need to import modules in other languages [create an Issue](https://github.com/vinpac/sublime-simple-import/issues).

## Examples

visibilityActions.js
```
export const SET_VISIBILITY_FILTER = 'SET_VISIBILITY_FILTER'
export const SHOW_ALL = 'SHOW_ALL'
export const SHOW_COMPLETED = 'SHOW_COMPLETED'
export const SHOW_ACTIVE = 'SHOW_ACTIVE'
```

VisibleTodoList.js
```
// SHOW_ALL *Ctrl+Alt+J*
import { SHOW_ALL } from '../actions/visibilityActions'

// SHOW_COMPLETED *Ctrl+Alt+J*
import { SHOW_ALL, SHOW_COMPLETED } from '../actions/visibilityActions'

// visibilityActions *Ctrl+Alt+J*
import visibilityActions, { SHOW_ALL, SHOW_COMPLETED } from '../actions/visibilityActions'

// req react *Ctrl+Alt+J*
const react = require("react")
```

Installation
-------------

You can find this plugin in Packages Control by the name of "Simple Import". You can also clone it in you packages folder.

 - Open the Command Palette and find `Browse Packages`.  Select it and the packages folder will open.
 - Clone this repository in this folder
	 - On Terminal, clone this repository: `git clone https://github.com/vinpac/sublime-simple-import.git`
	 - or Download this repository as `rar` and put the content inside the packages folder
