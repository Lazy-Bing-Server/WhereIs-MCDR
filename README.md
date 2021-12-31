**English** | [简体中文](README_zh.md)

Where Is
-------

A [MCDReforged](https://github.com/Fallen-Breath/MCDReforged) plugin, inspired by [Fallen_Breath's](https://github.com/Fallen-Breath) [Here](https://github.com/TISUnion/Here) and [Ivan-1F's](https://github.com/Ivan-1F) [Where](https://github.com/Ivan-1F/MCDReforged-Plugins/tree/master/where)

## Dependencies

[MinecraftDataAPI](https://github.com/MCDReforged/MinecraftDataAPI/)

[MCDReforged](https://github.com/Fallen-Breath/MCDReforged) >= 2.1.3

## Commands

`!!whereis` or `!!vris`（can be modified in config）：Show coordinate of other player

`-a` or `-s` arguments are allowed (can be called in one argument as `-as` or `-sa`)

`-a` means broadcasting coordinate to **a**ll the players and highlight target player

`-s` means **s**udo, allows querying coordinate of protected players

Both 2 arguments requires `admin` permission level in the config file of this plugin

## Config File

Several features can be modified with configuration file, which will be generated automatically in `config/where_is/config.json`

Calling `!!MCDR plg reload where_is` to reload is required to make it loaded after modifying

Here is the config items in the file

| Keys                      | Value type                     | Default value           | Introduction                                                 |
| ------------------------- | ------------------------------ | ----------------------- | ------------------------------------------------------------ |
| `command_prefix`          | `list`                         | `'!!vris', '!!whereis'` | Command prefix of this plugin                                |
| `permission_requirements` | `dict`(which includes 2 items) | In the following sheets | Minium permission of commands                                |
| `hightlight_time`         | `int`                          | `0`                     | Highlight player time when command with `-a` called          |
| `display_waypoints`       | `dict`(which includes 2 items) | In the following sheets | If the text would include waypoint text of minimap           |
| `query_timeout`           | `int`                          | `3`                     | Timeout of Minecraft Data API (seconds)                      |
| `click_to_teleport`       | `bool`                         | `true`                  | Allow player click to fill the teleport command (still requires operator permission) |
| `location_protection`     | `dict`(which includes 5 items) | In the following sheets | Player coordinate protection configuration                   |

In the sheet above, the items which have stable items is showing below:

| Keys of`permission_requirements` | Value type | Default value | Introduction                                                 |
| -------------------------------- | ---------- | ------------- | ------------------------------------------------------------ |
| `where_is`                       | `int`      | `1`           | Permissions which allows command calls without extra arguments |
| `admin`                          | `int`      | `3`           | Permissions which allows command calls with extra arguments  |

| Keys of`display_waypoints` | Value type | Default value | Introduction                                                 |
| -------------------------- | ---------- | ------------- | ------------------------------------------------------------ |
| `voxelmap`                 | `bool`     | `true`        | If it is `true` a text (`[+V]`) will be displayed, click to highlight the location, ctrl-click to add waypoint to [Voxelmap](https://www.curseforge.com/minecraft/mc-mods/voxelmap) |
| `xaero_minimap`            | `bool`     | `true`        | If it is `true` a text (`[+X]`) will be displayed, click to add waypoint to [Xaero's Minimap](https://chocolateminecraft.com/minimap2.php) |

| Keys of`location_protection` | Value type | Default value                                           | Introduction                                                 |
| ---------------------------- | ---------- |---------------------------------------------------------| ------------------------------------------------------------ |
| `enable_whitelist`           | `bool`     | `false`                                                 | Enable querying whitelist, which blocks the player **NOT** in this list being queried |
| `enable_blacklist`           | `bool`     | `true`                                                  | Enable querying whitelist, which blocks the player in this list being queried |
| `whitelist`                  | `list`     | empty list                                              | whitelist, which blocks the player **NOT** in this list being queried |
| `blacklist`                  | `list`     | empty list                                              | Enable querying whitelist, which blocks the player in this list being queried |
| `protected_text`             | `dict`     | `'en_us': 'He/She\'s in your heart!', 'zh_cn': 'Ta在你心里!'` | Text replied when querying blocked, supports language preference of MCDReforged |

## Example

![](img.png)
