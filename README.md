Simple Import v2.0.0-alpha
==========================

[![Join the chat at https://gitter.im/sublime-simple-import/Lobby](https://badges.gitter.im/sublime-simple-import/Lobby.svg)](https://gitter.im/sublime-simple-import/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

`Simple import` is a plugin for Sublime Text that imports your modules. Currently it works with Javascript and Python. If you need to import modules in other languages [create an Issue](https://github.com/vinpac/sublime-simple-import/issues).

![example gif](https://raw.githubusercontent.com/vinpac/sublime-simple-import/master/assets/example.gif)


## Examples
Note: These examples are Javascript-only. Simple Import works with Scss and Python too at the moment.

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


Settings
--------

### Javascript

**extensions**  (Array) : Extensions to match. Default: `[".js", ".jsx"]`

**remove_extensions**  (Array) : Remove extensions from path. Default: `[".js"]`

**extra_extensions**  (Array) : Extensions to match, but SI will not look into these files for submodules. Default: `[".png", ".jpg", ".jpeg", ".svg", ".json", ".gif", ".css", ".scss", ".less"]`

**ignore**  (Array) : Paths to be ignored when crawling for modules.

**require_by_default**  (Boolean) : Prefer `require` than `import`. Default: `False`

**add_semicolon**  (Boolean) : Add `;` at the end of the import. Default: `True`

**es5**  (Boolean) : Will force `require_by_default`, `add_semicolon` and will use `var` instead of `const`. Default: False

### SCSS

**extensions**  (Array) : Extensions to match. Default: `[".scss"]`

**extra_extensions**  (Array) : Extensions of files to match and import as `url(<path>)`. Default: `[".jpg", ".png", ".gif", ".svg"]`

**ignore**  (Array) : Paths to be ignored when crawling for modules.

### Python

**extensions**  (Array) : Extensions to match. Default: `[".py"]`

**remove_extensions**  (Array) : Remove extensions from path. Default: `[".py"]`

**ignore**  (Array) : Paths to be ignored when crawling for modules.
