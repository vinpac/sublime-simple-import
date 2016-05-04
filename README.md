Simple Import v2.0.0
===================

`Simple import` is a plugin for Sublime Text that imports your modules. Just select select the module you want to import and select "Simple Import: insert imports". You can import as many modules you want at once.

Now this plugin will work with context and not only with JS. Actually, now, we generate the import based on a json that stores all the information about how the importation in each syntax works:

```
{
  "javascript": {
    "syntax": "javascript",
    "handlers" : {
      "import": {
        "default": true,
        "match": [
          "import {variable}",
          "import {variable} from {module}"
        ],
        "result": "import {variable} from \"{module}\""
      },
      "require": {
        "match": [
          "(const|let|var) {variable}",
          "(const|let|var) {variable} = {module}"
        ],
        "result": "const {variable} = require(\"{module}\")"
      }
    }
  }
```
