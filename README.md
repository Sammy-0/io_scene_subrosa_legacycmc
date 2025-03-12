# Sub Rosa Tools

A comprehensive Blender extension for import/export of file formats from the game [Sub Rosa](https://store.steampowered.com/app/272230/Sub_Rosa) by [Cryptic Sea](https://www.crypticsea.com/). Modernized version of the [original io_scene_subrosa](https://github.com/jdbool/io_scene_subrosa).

This extension supports the following file formats:

| Format                    | Import  | Export |
|---------------------------|:-------:|:------:|
| Character (.cmc)          | ✅      | ✅    |
| Object (.cmo)             | ✅      | ✅    |
| Item (.itm)               | ✅      | ❌    |
| Vehicle (.sbv)            | ✅      | ❌    |
| Legacy Object (.sit)      | ✅      | ❌    |
| Interactive Object (.it3) | ❌      | ❌    |

## Development

Create a Python venv, and run: `pip install -r requirements.txt`
Following that, open the project in VS Code or your preferred editor. You should have types/intellisense (with the appropriate Python extension/LSP).

This is a Blender extension, ported from the original add-on using the legacy format.

## Credits

[jdbool/Mike](https://github.com/jdbool) - Creator of the original [io_scene_subrosa addon](https://github.com/jdbool/io_scene_subrosa)
[checkraisefold](https://github.com/checkraisefold) - Modernization and addition of extra support, especially for the cmc format
