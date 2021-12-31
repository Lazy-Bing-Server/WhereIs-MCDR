**简体中文** | [English](README.md)

Where Is
-------

一个 [MCDReforged](https://github.com/Fallen-Breath/MCDReforged) 的插件, 受到 [Fallen_Breath](https://github.com/Fallen-Breath) 的 [Here](https://github.com/TISUnion/Here) and [Ivan-1F](https://github.com/Ivan-1F) 的 [Where](https://github.com/Ivan-1F/MCDReforged-Plugins/tree/master/where) 启发

## 依赖

[MinecraftDataAPI](https://github.com/MCDReforged/MinecraftDataAPI/)

[MCDReforged](https://github.com/Fallen-Breath/MCDReforged) >= 2.1.3

## 指令

`!!whereis` 或者 `!!vris`（可在配置文件中修改）：显示一个其他玩家的坐标。

可以加`-a` 或者 `-s`（可以合成一个参数写作 `-as` 或者 `-sa`）。

`-a` 意为向所有(**a**ll)玩家发送坐标并高亮该玩家；

`-s` 意为提权(**s**udo)，允许查看受保护的玩家的坐标。

两个参数均需要插件配置中设置的 `admin` 等级来执行。

## 配置文件

部分特性可由配置文件控制，默认自动生成于 `config/where_is/config.json`。

修改配置文件之后需要使用`!!MCDR plg reload here`重载方可生效。

以下为配置文件内容

| 键                        | 值的类型              | 默认值                  | 说明                                    |
| ------------------------- | --------------------- | ----------------------- | --------------------------------------- |
| `command_prefix`          | `list`                | `'!!vris', '!!whereis'` | 插件指令前缀                            |
| `permission_requirements` | `dict`(含固定的2个值) | 见下表                  | 指令要求的最小权限等级                  |
| `hightlight_time`         | `int`                 | `0`                     | 当包含 `-a` 参数时高亮玩家的时间        |
| `display_waypoints`       | `dict`(含固定的2个值) | 见下表                  | 是否显示小地图坐标点                    |
| `query_timeout`           | `int`                 | `3`                     | Minecraft Data API的超时时间            |
| `click_to_teleport`       | `bool`                | `true`                  | 允许玩家点击补全传送指令 (仍需OP以执行) |
| `location_protection`     | `dict`(含固定的5个值) | 见下表                  | 玩家坐标保护相关设定                    |

上述提到的含固定键值对的的配置项如下:

| `permission_requirements` 的键 | 值类型 | 默认值 | 说明                                   |
| ------------------------------ | ------ | ------ | -------------------------------------- |
| `where_is`                     | `int`  | `1`    | 玩家可执行不含参数的本插件指令的最小值 |
| `admin`                        | `int`  | `3`    | 玩家可执行含参数的本插件指令的最小值   |

| `display_waypoints`的键 | 值类型 | 默认值 | 说明                                                         |
| ----------------------- | ------ | ------ | ------------------------------------------------------------ |
| `voxelmap`              | `bool` | `true` | 为 `true` 时显示一个附带点击事件的文本 (`[+V]`) 点击高亮坐标，Ctrl点击添加坐标点到 [Voxelmap](https://www.curseforge.com/minecraft/mc-mods/voxelmap) |
| `xaero_minimap`         | `bool` | `true` | 为 `true` 时显示一个附带点击事件的文本 (`[+x]`) , 点击添加路径点到 [Xaero's Minimap](https://chocolateminecraft.com/minimap2.php) |

| `location_protection` 的键 | 值类型 | 默认值                                                       | 说明                                                       |
| -------------------------- | ------ | ------------------------------------------------------------ | ---------------------------------------------------------- |
| `enable_whitelist`         | `bool` | `false`                                                      | 启用查询白名单，启用时限制白名单外的玩家被查询             |
| `enable_blacklist`         | `bool` | `true`                                                       | 启用查询黑名单，启用时限制黑名单内的玩家被查询             |
| `whitelist`                | `list` | 空列表                                                       | 白名单，限制除此之外的玩家被查询                           |
| `blacklist`                | `list` | 空列表                                                       | 黑名单，限制该列表内的玩家被查询                           |
| `protected_text`           | `dict` | `'en_us': 'He/She\'s in your heart!' 'zh_cn': 'Ta在你心里!'` | 当玩家被阻止查询时显示的信息，提供了MCDR语言偏好设置的支持 |

## 示例

![](img.png)
