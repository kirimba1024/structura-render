# Аудит рендера блоков Minecraft Java 26.2

Проверено: **1198 blockstate-файлов**. **JSON: 1**, **JSON + составная: 1**, **клиентский JSON: 1100**, **намеренно скрыт: 7**, **составная: 89**

Обычные блоки сверяются пакетно с клиентскими blockstate/model JSON: variants, multipart, AND/OR, вращения элементов и UV, uvlock и weighted-варианты. Это точнее ручного пересказа тысячи страниц. Общие правила и исключения сверены с [форматом blockstates](https://minecraft.wiki/w/Blockstates_definition/format), [неремоделируемыми блоками](https://minecraft.wiki/w/Template:Non-remodellable_blocks) и [ограничениями structure renderer](https://minecraft.wiki/w/Template:Block_structure_renderer).

Серые служебные tint-текстуры получают фиксированный осмысленный цвет: биомная трава/листва/вода, лилии, стебли и мощность redstone. Динамические тексты, узоры, пользовательские скины и анимация отмечены как остаточные ограничения, а не маскируются словом «точно».

| Блок | Геометрия | Текстура/цвет | Проверка и остаток |
|---|---|---|---|
| minecraft:acacia_button | клиентский JSON | block texture | variants, uvlock |
| minecraft:acacia_door | клиентский JSON | block texture | variants |
| minecraft:acacia_fence | клиентский JSON | block texture | multipart, uvlock |
| minecraft:acacia_fence_gate | клиентский JSON | block texture | variants, uvlock |
| minecraft:acacia_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:acacia_leaves | клиентский JSON | block texture + явный tint | variants |
| minecraft:acacia_log | клиентский JSON | block texture | variants |
| minecraft:acacia_planks | клиентский JSON | block texture | variants |
| minecraft:acacia_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:acacia_sapling | клиентский JSON | block texture | variants |
| minecraft:acacia_shelf | клиентский JSON | block texture | multipart |
| minecraft:acacia_sign | клиентский JSON | block texture | variants |
| minecraft:acacia_slab | клиентский JSON | block texture | variants |
| minecraft:acacia_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:acacia_trapdoor | клиентский JSON | block texture | variants |
| minecraft:acacia_wall_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:acacia_wall_sign | клиентский JSON | block texture | variants |
| minecraft:acacia_wood | клиентский JSON | block texture | variants |
| minecraft:activator_rail | клиентский JSON | block texture | variants |
| minecraft:air | намеренно скрыт | — | воздух/технический блок |
| minecraft:allium | клиентский JSON | block texture | variants |
| minecraft:amethyst_block | клиентский JSON | block texture | variants |
| minecraft:amethyst_cluster | клиентский JSON | block texture | variants |
| minecraft:ancient_debris | клиентский JSON | block texture | variants |
| minecraft:andesite | клиентский JSON | block texture | variants |
| minecraft:andesite_slab | клиентский JSON | block texture | variants |
| minecraft:andesite_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:andesite_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:anvil | клиентский JSON | block texture | variants |
| minecraft:attached_melon_stem | клиентский JSON | block texture + явный tint | variants |
| minecraft:attached_pumpkin_stem | клиентский JSON | block texture + явный tint | variants |
| minecraft:azalea | клиентский JSON | block texture | variants |
| minecraft:azalea_leaves | клиентский JSON | block texture | variants |
| minecraft:azure_bluet | клиентский JSON | block texture | variants |
| minecraft:bamboo | клиентский JSON | block texture + явный tint | multipart |
| minecraft:bamboo_block | клиентский JSON | block texture | variants |
| minecraft:bamboo_button | клиентский JSON | block texture | variants, uvlock |
| minecraft:bamboo_door | клиентский JSON | block texture | variants |
| minecraft:bamboo_fence | клиентский JSON | block texture | multipart |
| minecraft:bamboo_fence_gate | клиентский JSON | block texture | variants |
| minecraft:bamboo_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:bamboo_mosaic | клиентский JSON | block texture | variants |
| minecraft:bamboo_mosaic_slab | клиентский JSON | block texture | variants |
| minecraft:bamboo_mosaic_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:bamboo_planks | клиентский JSON | block texture | variants |
| minecraft:bamboo_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:bamboo_sapling | клиентский JSON | block texture + явный tint | variants |
| minecraft:bamboo_shelf | клиентский JSON | block texture | multipart |
| minecraft:bamboo_sign | клиентский JSON | block texture | variants |
| minecraft:bamboo_slab | клиентский JSON | block texture | variants |
| minecraft:bamboo_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:bamboo_trapdoor | клиентский JSON | block texture | variants |
| minecraft:bamboo_wall_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:bamboo_wall_sign | клиентский JSON | block texture | variants |
| minecraft:barrel | клиентский JSON | block texture | variants |
| minecraft:barrier | намеренно скрыт | — | воздух/технический блок |
| minecraft:basalt | клиентский JSON | block texture | variants |
| minecraft:beacon | клиентский JSON | block texture | variants |
| minecraft:bedrock | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:bee_nest | клиентский JSON | block texture | variants |
| minecraft:beehive | клиентский JSON | block texture | variants |
| minecraft:beetroots | клиентский JSON | block texture | variants |
| minecraft:bell | JSON + составная | entity/effect texture | JSON-крепление и entity-текстура колокола |
| minecraft:big_dripleaf | клиентский JSON | block texture | variants |
| minecraft:big_dripleaf_stem | клиентский JSON | block texture | variants |
| minecraft:birch_button | клиентский JSON | block texture | variants, uvlock |
| minecraft:birch_door | клиентский JSON | block texture | variants |
| minecraft:birch_fence | клиентский JSON | block texture | multipart, uvlock |
| minecraft:birch_fence_gate | клиентский JSON | block texture | variants, uvlock |
| minecraft:birch_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:birch_leaves | клиентский JSON | block texture + явный tint | variants |
| minecraft:birch_log | клиентский JSON | block texture | variants |
| minecraft:birch_planks | клиентский JSON | block texture | variants |
| minecraft:birch_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:birch_sapling | клиентский JSON | block texture | variants |
| minecraft:birch_shelf | клиентский JSON | block texture | multipart |
| minecraft:birch_sign | клиентский JSON | block texture | variants |
| minecraft:birch_slab | клиентский JSON | block texture | variants |
| minecraft:birch_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:birch_trapdoor | клиентский JSON | block texture | variants |
| minecraft:birch_wall_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:birch_wall_sign | клиентский JSON | block texture | variants |
| minecraft:birch_wood | клиентский JSON | block texture | variants |
| minecraft:black_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:black_bed | клиентский JSON | block texture | variants |
| minecraft:black_candle | клиентский JSON | block texture | variants |
| minecraft:black_candle_cake | клиентский JSON | block texture | variants |
| minecraft:black_carpet | клиентский JSON | block texture | variants |
| minecraft:black_concrete | клиентский JSON | block texture | variants |
| minecraft:black_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:black_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:black_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:black_stained_glass | клиентский JSON | block texture | variants |
| minecraft:black_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:black_terracotta | клиентский JSON | block texture | variants |
| minecraft:black_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:black_wool | клиентский JSON | block texture | variants |
| minecraft:blackstone | клиентский JSON | block texture | variants |
| minecraft:blackstone_slab | клиентский JSON | block texture | variants |
| minecraft:blackstone_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:blackstone_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:blast_furnace | клиентский JSON | block texture | variants |
| minecraft:blue_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:blue_bed | клиентский JSON | block texture | variants |
| minecraft:blue_candle | клиентский JSON | block texture | variants |
| minecraft:blue_candle_cake | клиентский JSON | block texture | variants |
| minecraft:blue_carpet | клиентский JSON | block texture | variants |
| minecraft:blue_concrete | клиентский JSON | block texture | variants |
| minecraft:blue_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:blue_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:blue_ice | клиентский JSON | block texture | variants |
| minecraft:blue_orchid | клиентский JSON | block texture | variants |
| minecraft:blue_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:blue_stained_glass | клиентский JSON | block texture | variants |
| minecraft:blue_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:blue_terracotta | клиентский JSON | block texture | variants |
| minecraft:blue_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:blue_wool | клиентский JSON | block texture | variants |
| minecraft:bone_block | клиентский JSON | block texture | variants |
| minecraft:bookshelf | клиентский JSON | block texture | variants |
| minecraft:brain_coral | клиентский JSON | block texture | variants |
| minecraft:brain_coral_block | клиентский JSON | block texture | variants |
| minecraft:brain_coral_fan | клиентский JSON | block texture | variants |
| minecraft:brain_coral_wall_fan | клиентский JSON | block texture | variants |
| minecraft:brewing_stand | клиентский JSON | block texture | multipart |
| minecraft:brick_slab | клиентский JSON | block texture | variants |
| minecraft:brick_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:brick_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:bricks | клиентский JSON | block texture | variants |
| minecraft:brown_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:brown_bed | клиентский JSON | block texture | variants |
| minecraft:brown_candle | клиентский JSON | block texture | variants |
| minecraft:brown_candle_cake | клиентский JSON | block texture | variants |
| minecraft:brown_carpet | клиентский JSON | block texture | variants |
| minecraft:brown_concrete | клиентский JSON | block texture | variants |
| minecraft:brown_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:brown_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:brown_mushroom | клиентский JSON | block texture | variants |
| minecraft:brown_mushroom_block | клиентский JSON | block texture | multipart, uvlock |
| minecraft:brown_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:brown_stained_glass | клиентский JSON | block texture | variants |
| minecraft:brown_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:brown_terracotta | клиентский JSON | block texture | variants |
| minecraft:brown_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:brown_wool | клиентский JSON | block texture | variants |
| minecraft:bubble_column | составная | block texture + цвет | уровень жидкости; статичный кадр течения |
| minecraft:bubble_coral | клиентский JSON | block texture | variants |
| minecraft:bubble_coral_block | клиентский JSON | block texture | variants |
| minecraft:bubble_coral_fan | клиентский JSON | block texture | variants |
| minecraft:bubble_coral_wall_fan | клиентский JSON | block texture | variants |
| minecraft:budding_amethyst | клиентский JSON | block texture | variants |
| minecraft:bush | клиентский JSON | block texture + явный tint | variants |
| minecraft:cactus | клиентский JSON | block texture | variants |
| minecraft:cactus_flower | клиентский JSON | block texture | variants |
| minecraft:cake | клиентский JSON | block texture | variants |
| minecraft:calcite | клиентский JSON | block texture | variants |
| minecraft:calibrated_sculk_sensor | клиентский JSON | block texture | variants |
| minecraft:campfire | клиентский JSON | block texture | variants |
| minecraft:candle | клиентский JSON | block texture | variants |
| minecraft:candle_cake | клиентский JSON | block texture | variants |
| minecraft:carrots | клиентский JSON | block texture | variants |
| minecraft:cartography_table | клиентский JSON | block texture | variants |
| minecraft:carved_pumpkin | клиентский JSON | block texture | variants |
| minecraft:cauldron | клиентский JSON | block texture | variants |
| minecraft:cave_air | намеренно скрыт | — | воздух/технический блок |
| minecraft:cave_vines | клиентский JSON | block texture | variants |
| minecraft:cave_vines_plant | клиентский JSON | block texture | variants |
| minecraft:chain_command_block | клиентский JSON | block texture | variants |
| minecraft:cherry_button | клиентский JSON | block texture | variants, uvlock |
| minecraft:cherry_door | клиентский JSON | block texture | variants |
| minecraft:cherry_fence | клиентский JSON | block texture | multipart, uvlock |
| minecraft:cherry_fence_gate | клиентский JSON | block texture | variants, uvlock |
| minecraft:cherry_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:cherry_leaves | клиентский JSON | block texture + явный tint | variants |
| minecraft:cherry_log | клиентский JSON | block texture | variants |
| minecraft:cherry_planks | клиентский JSON | block texture | variants |
| minecraft:cherry_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:cherry_sapling | клиентский JSON | block texture | variants |
| minecraft:cherry_shelf | клиентский JSON | block texture | multipart |
| minecraft:cherry_sign | клиентский JSON | block texture | variants |
| minecraft:cherry_slab | клиентский JSON | block texture | variants |
| minecraft:cherry_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:cherry_trapdoor | клиентский JSON | block texture | variants |
| minecraft:cherry_wall_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:cherry_wall_sign | клиентский JSON | block texture | variants |
| minecraft:cherry_wood | клиентский JSON | block texture | variants |
| minecraft:chest | составная | entity/effect texture | тип, направление и стадия меди |
| minecraft:chipped_anvil | клиентский JSON | block texture | variants |
| minecraft:chiseled_bookshelf | клиентский JSON | block texture | multipart, uvlock |
| minecraft:chiseled_cinnabar | клиентский JSON | block texture | variants |
| minecraft:chiseled_copper | клиентский JSON | block texture | variants |
| minecraft:chiseled_deepslate | клиентский JSON | block texture | variants |
| minecraft:chiseled_nether_bricks | клиентский JSON | block texture | variants |
| minecraft:chiseled_polished_blackstone | клиентский JSON | block texture | variants |
| minecraft:chiseled_quartz_block | клиентский JSON | block texture | variants |
| minecraft:chiseled_red_sandstone | клиентский JSON | block texture | variants |
| minecraft:chiseled_resin_bricks | клиентский JSON | block texture | variants |
| minecraft:chiseled_sandstone | клиентский JSON | block texture | variants |
| minecraft:chiseled_stone_bricks | клиентский JSON | block texture | variants |
| minecraft:chiseled_sulfur | клиентский JSON | block texture | variants |
| minecraft:chiseled_tuff | клиентский JSON | block texture | variants |
| minecraft:chiseled_tuff_bricks | клиентский JSON | block texture | variants |
| minecraft:chorus_flower | клиентский JSON | block texture | variants |
| minecraft:chorus_plant | клиентский JSON | block texture | multipart, uvlock |
| minecraft:cinnabar | клиентский JSON | block texture | variants |
| minecraft:cinnabar_brick_slab | клиентский JSON | block texture | variants |
| minecraft:cinnabar_brick_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:cinnabar_brick_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:cinnabar_bricks | клиентский JSON | block texture | variants |
| minecraft:cinnabar_slab | клиентский JSON | block texture | variants |
| minecraft:cinnabar_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:cinnabar_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:clay | клиентский JSON | block texture | variants |
| minecraft:closed_eyeblossom | клиентский JSON | block texture | variants |
| minecraft:coal_block | клиентский JSON | block texture | variants |
| minecraft:coal_ore | клиентский JSON | block texture | variants |
| minecraft:coarse_dirt | клиентский JSON | block texture | variants |
| minecraft:cobbled_deepslate | клиентский JSON | block texture | variants |
| minecraft:cobbled_deepslate_slab | клиентский JSON | block texture | variants |
| minecraft:cobbled_deepslate_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:cobbled_deepslate_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:cobblestone | клиентский JSON | block texture | variants |
| minecraft:cobblestone_slab | клиентский JSON | block texture | variants |
| minecraft:cobblestone_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:cobblestone_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:cobweb | клиентский JSON | block texture | variants |
| minecraft:cocoa | клиентский JSON | block texture | variants |
| minecraft:command_block | клиентский JSON | block texture | variants |
| minecraft:comparator | клиентский JSON | block texture | variants |
| minecraft:composter | клиентский JSON | block texture | multipart |
| minecraft:conduit | составная | entity/effect texture | ядро; без активной анимации клетки/ветра |
| minecraft:copper_bars | клиентский JSON | block texture | multipart |
| minecraft:copper_block | клиентский JSON | block texture | variants |
| minecraft:copper_bulb | клиентский JSON | block texture | variants |
| minecraft:copper_chain | клиентский JSON | block texture | variants |
| minecraft:copper_chest | составная | entity/effect texture | тип, направление и стадия меди |
| minecraft:copper_door | клиентский JSON | block texture | variants |
| minecraft:copper_golem_statue | составная | entity/effect texture | составная статуя и стадия окисления |
| minecraft:copper_grate | клиентский JSON | block texture | variants |
| minecraft:copper_lantern | клиентский JSON | block texture | variants |
| minecraft:copper_ore | клиентский JSON | block texture | variants |
| minecraft:copper_torch | клиентский JSON | block texture | variants |
| minecraft:copper_trapdoor | клиентский JSON | block texture | variants |
| minecraft:copper_wall_torch | клиентский JSON | block texture | variants |
| minecraft:cornflower | клиентский JSON | block texture | variants |
| minecraft:cracked_deepslate_bricks | клиентский JSON | block texture | variants |
| minecraft:cracked_deepslate_tiles | клиентский JSON | block texture | variants |
| minecraft:cracked_nether_bricks | клиентский JSON | block texture | variants |
| minecraft:cracked_polished_blackstone_bricks | клиентский JSON | block texture | variants |
| minecraft:cracked_stone_bricks | клиентский JSON | block texture | variants |
| minecraft:crafter | клиентский JSON | block texture | variants |
| minecraft:crafting_table | клиентский JSON | block texture | variants |
| minecraft:creaking_heart | клиентский JSON | block texture | variants |
| minecraft:creeper_head | составная | entity/effect texture | моб-скин; player profile использует Steve |
| minecraft:creeper_wall_head | составная | entity/effect texture | моб-скин; player profile использует Steve |
| minecraft:crimson_button | клиентский JSON | block texture | variants, uvlock |
| minecraft:crimson_door | клиентский JSON | block texture | variants |
| minecraft:crimson_fence | клиентский JSON | block texture | multipart, uvlock |
| minecraft:crimson_fence_gate | клиентский JSON | block texture | variants, uvlock |
| minecraft:crimson_fungus | клиентский JSON | block texture | variants |
| minecraft:crimson_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:crimson_hyphae | клиентский JSON | block texture | variants |
| minecraft:crimson_nylium | клиентский JSON | block texture | variants |
| minecraft:crimson_planks | клиентский JSON | block texture | variants |
| minecraft:crimson_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:crimson_roots | клиентский JSON | block texture | variants |
| minecraft:crimson_shelf | клиентский JSON | block texture | multipart |
| minecraft:crimson_sign | клиентский JSON | block texture | variants |
| minecraft:crimson_slab | клиентский JSON | block texture | variants |
| minecraft:crimson_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:crimson_stem | клиентский JSON | block texture | variants |
| minecraft:crimson_trapdoor | клиентский JSON | block texture | variants |
| minecraft:crimson_wall_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:crimson_wall_sign | клиентский JSON | block texture | variants |
| minecraft:crying_obsidian | клиентский JSON | block texture | variants |
| minecraft:cut_copper | клиентский JSON | block texture | variants |
| minecraft:cut_copper_slab | клиентский JSON | block texture | variants |
| minecraft:cut_copper_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:cut_red_sandstone | клиентский JSON | block texture | variants |
| minecraft:cut_red_sandstone_slab | клиентский JSON | block texture | variants |
| minecraft:cut_sandstone | клиентский JSON | block texture | variants |
| minecraft:cut_sandstone_slab | клиентский JSON | block texture | variants |
| minecraft:cyan_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:cyan_bed | клиентский JSON | block texture | variants |
| minecraft:cyan_candle | клиентский JSON | block texture | variants |
| minecraft:cyan_candle_cake | клиентский JSON | block texture | variants |
| minecraft:cyan_carpet | клиентский JSON | block texture | variants |
| minecraft:cyan_concrete | клиентский JSON | block texture | variants |
| minecraft:cyan_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:cyan_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:cyan_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:cyan_stained_glass | клиентский JSON | block texture | variants |
| minecraft:cyan_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:cyan_terracotta | клиентский JSON | block texture | variants |
| minecraft:cyan_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:cyan_wool | клиентский JSON | block texture | variants |
| minecraft:damaged_anvil | клиентский JSON | block texture | variants |
| minecraft:dandelion | клиентский JSON | block texture | variants |
| minecraft:dark_oak_button | клиентский JSON | block texture | variants, uvlock |
| minecraft:dark_oak_door | клиентский JSON | block texture | variants |
| minecraft:dark_oak_fence | клиентский JSON | block texture | multipart, uvlock |
| minecraft:dark_oak_fence_gate | клиентский JSON | block texture | variants, uvlock |
| minecraft:dark_oak_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:dark_oak_leaves | клиентский JSON | block texture + явный tint | variants |
| minecraft:dark_oak_log | клиентский JSON | block texture | variants |
| minecraft:dark_oak_planks | клиентский JSON | block texture | variants |
| minecraft:dark_oak_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:dark_oak_sapling | клиентский JSON | block texture | variants |
| minecraft:dark_oak_shelf | клиентский JSON | block texture | multipart |
| minecraft:dark_oak_sign | клиентский JSON | block texture | variants |
| minecraft:dark_oak_slab | клиентский JSON | block texture | variants |
| minecraft:dark_oak_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:dark_oak_trapdoor | клиентский JSON | block texture | variants |
| minecraft:dark_oak_wall_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:dark_oak_wall_sign | клиентский JSON | block texture | variants |
| minecraft:dark_oak_wood | клиентский JSON | block texture | variants |
| minecraft:dark_prismarine | клиентский JSON | block texture | variants |
| minecraft:dark_prismarine_slab | клиентский JSON | block texture | variants |
| minecraft:dark_prismarine_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:daylight_detector | клиентский JSON | block texture | variants |
| minecraft:dead_brain_coral | клиентский JSON | block texture | variants |
| minecraft:dead_brain_coral_block | клиентский JSON | block texture | variants |
| minecraft:dead_brain_coral_fan | клиентский JSON | block texture | variants |
| minecraft:dead_brain_coral_wall_fan | клиентский JSON | block texture | variants |
| minecraft:dead_bubble_coral | клиентский JSON | block texture | variants |
| minecraft:dead_bubble_coral_block | клиентский JSON | block texture | variants |
| minecraft:dead_bubble_coral_fan | клиентский JSON | block texture | variants |
| minecraft:dead_bubble_coral_wall_fan | клиентский JSON | block texture | variants |
| minecraft:dead_bush | клиентский JSON | block texture | variants |
| minecraft:dead_fire_coral | клиентский JSON | block texture | variants |
| minecraft:dead_fire_coral_block | клиентский JSON | block texture | variants |
| minecraft:dead_fire_coral_fan | клиентский JSON | block texture | variants |
| minecraft:dead_fire_coral_wall_fan | клиентский JSON | block texture | variants |
| minecraft:dead_horn_coral | клиентский JSON | block texture | variants |
| minecraft:dead_horn_coral_block | клиентский JSON | block texture | variants |
| minecraft:dead_horn_coral_fan | клиентский JSON | block texture | variants |
| minecraft:dead_horn_coral_wall_fan | клиентский JSON | block texture | variants |
| minecraft:dead_tube_coral | клиентский JSON | block texture | variants |
| minecraft:dead_tube_coral_block | клиентский JSON | block texture | variants |
| minecraft:dead_tube_coral_fan | клиентский JSON | block texture | variants |
| minecraft:dead_tube_coral_wall_fan | клиентский JSON | block texture | variants |
| minecraft:decorated_pot | составная | entity/effect texture | корпус/горло; без NBT-рисунков черепков |
| minecraft:deepslate | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:deepslate_brick_slab | клиентский JSON | block texture | variants |
| minecraft:deepslate_brick_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:deepslate_brick_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:deepslate_bricks | клиентский JSON | block texture | variants |
| minecraft:deepslate_coal_ore | клиентский JSON | block texture | variants |
| minecraft:deepslate_copper_ore | клиентский JSON | block texture | variants |
| minecraft:deepslate_diamond_ore | клиентский JSON | block texture | variants |
| minecraft:deepslate_emerald_ore | клиентский JSON | block texture | variants |
| minecraft:deepslate_gold_ore | клиентский JSON | block texture | variants |
| minecraft:deepslate_iron_ore | клиентский JSON | block texture | variants |
| minecraft:deepslate_lapis_ore | клиентский JSON | block texture | variants |
| minecraft:deepslate_redstone_ore | клиентский JSON | block texture | variants |
| minecraft:deepslate_tile_slab | клиентский JSON | block texture | variants |
| minecraft:deepslate_tile_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:deepslate_tile_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:deepslate_tiles | клиентский JSON | block texture | variants |
| minecraft:detector_rail | клиентский JSON | block texture | variants |
| minecraft:diamond_block | клиентский JSON | block texture | variants |
| minecraft:diamond_ore | клиентский JSON | block texture | variants |
| minecraft:diorite | клиентский JSON | block texture | variants |
| minecraft:diorite_slab | клиентский JSON | block texture | variants |
| minecraft:diorite_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:diorite_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:dirt | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:dirt_path | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:dispenser | клиентский JSON | block texture | variants |
| minecraft:dragon_egg | клиентский JSON | block texture | variants |
| minecraft:dragon_head | составная | entity/effect texture | моб-скин; player profile использует Steve |
| minecraft:dragon_wall_head | составная | entity/effect texture | моб-скин; player profile использует Steve |
| minecraft:dried_ghast | клиентский JSON | block texture | variants |
| minecraft:dried_kelp_block | клиентский JSON | block texture | variants |
| minecraft:dripstone_block | клиентский JSON | block texture | variants |
| minecraft:dropper | клиентский JSON | block texture | variants |
| minecraft:emerald_block | клиентский JSON | block texture | variants |
| minecraft:emerald_ore | клиентский JSON | block texture | variants |
| minecraft:enchanting_table | клиентский JSON | block texture | variants |
| minecraft:end_gateway | составная | entity/effect texture | детерминированный starfield без анимации |
| minecraft:end_portal | составная | entity/effect texture | детерминированный starfield без анимации |
| minecraft:end_portal_frame | клиентский JSON | block texture | variants |
| minecraft:end_rod | клиентский JSON | block texture | variants |
| minecraft:end_stone | клиентский JSON | block texture | variants |
| minecraft:end_stone_brick_slab | клиентский JSON | block texture | variants |
| minecraft:end_stone_brick_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:end_stone_brick_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:end_stone_bricks | клиентский JSON | block texture | variants |
| minecraft:ender_chest | составная | entity/effect texture | тип, направление и стадия меди |
| minecraft:exposed_chiseled_copper | клиентский JSON | block texture | variants |
| minecraft:exposed_copper | клиентский JSON | block texture | variants |
| minecraft:exposed_copper_bars | клиентский JSON | block texture | multipart |
| minecraft:exposed_copper_bulb | клиентский JSON | block texture | variants |
| minecraft:exposed_copper_chain | клиентский JSON | block texture | variants |
| minecraft:exposed_copper_chest | составная | entity/effect texture | тип, направление и стадия меди |
| minecraft:exposed_copper_door | клиентский JSON | block texture | variants |
| minecraft:exposed_copper_golem_statue | составная | entity/effect texture | составная статуя и стадия окисления |
| minecraft:exposed_copper_grate | клиентский JSON | block texture | variants |
| minecraft:exposed_copper_lantern | клиентский JSON | block texture | variants |
| minecraft:exposed_copper_trapdoor | клиентский JSON | block texture | variants |
| minecraft:exposed_cut_copper | клиентский JSON | block texture | variants |
| minecraft:exposed_cut_copper_slab | клиентский JSON | block texture | variants |
| minecraft:exposed_cut_copper_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:exposed_lightning_rod | клиентский JSON | block texture | variants |
| minecraft:farmland | клиентский JSON | block texture | variants |
| minecraft:fern | клиентский JSON | block texture + явный tint | variants |
| minecraft:fire | клиентский JSON | block texture | multipart |
| minecraft:fire_coral | клиентский JSON | block texture | variants |
| minecraft:fire_coral_block | клиентский JSON | block texture | variants |
| minecraft:fire_coral_fan | клиентский JSON | block texture | variants |
| minecraft:fire_coral_wall_fan | клиентский JSON | block texture | variants |
| minecraft:firefly_bush | клиентский JSON | block texture | variants |
| minecraft:fletching_table | клиентский JSON | block texture | variants |
| minecraft:flower_pot | клиентский JSON | block texture | variants |
| minecraft:flowering_azalea | клиентский JSON | block texture | variants |
| minecraft:flowering_azalea_leaves | клиентский JSON | block texture | variants |
| minecraft:frogspawn | клиентский JSON | block texture | variants |
| minecraft:frosted_ice | клиентский JSON | block texture | variants |
| minecraft:furnace | клиентский JSON | block texture | variants |
| minecraft:gilded_blackstone | клиентский JSON | block texture | variants |
| minecraft:glass | клиентский JSON | block texture | variants |
| minecraft:glass_pane | клиентский JSON | block texture | multipart |
| minecraft:glow_item_frame | клиентский JSON | block texture | variants |
| minecraft:glow_lichen | клиентский JSON | block texture | multipart, uvlock |
| minecraft:glowstone | клиентский JSON | block texture | variants |
| minecraft:gold_block | клиентский JSON | block texture | variants |
| minecraft:gold_ore | клиентский JSON | block texture | variants |
| minecraft:golden_dandelion | клиентский JSON | block texture | variants |
| minecraft:granite | клиентский JSON | block texture | variants |
| minecraft:granite_slab | клиентский JSON | block texture | variants |
| minecraft:granite_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:granite_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:grass_block | клиентский JSON | block texture + явный tint | variants, стабильный weighted-вариант |
| minecraft:gravel | клиентский JSON | block texture | variants |
| minecraft:gray_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:gray_bed | клиентский JSON | block texture | variants |
| minecraft:gray_candle | клиентский JSON | block texture | variants |
| minecraft:gray_candle_cake | клиентский JSON | block texture | variants |
| minecraft:gray_carpet | клиентский JSON | block texture | variants |
| minecraft:gray_concrete | клиентский JSON | block texture | variants |
| minecraft:gray_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:gray_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:gray_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:gray_stained_glass | клиентский JSON | block texture | variants |
| minecraft:gray_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:gray_terracotta | клиентский JSON | block texture | variants |
| minecraft:gray_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:gray_wool | клиентский JSON | block texture | variants |
| minecraft:green_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:green_bed | клиентский JSON | block texture | variants |
| minecraft:green_candle | клиентский JSON | block texture | variants |
| minecraft:green_candle_cake | клиентский JSON | block texture | variants |
| minecraft:green_carpet | клиентский JSON | block texture | variants |
| minecraft:green_concrete | клиентский JSON | block texture | variants |
| minecraft:green_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:green_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:green_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:green_stained_glass | клиентский JSON | block texture | variants |
| minecraft:green_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:green_terracotta | клиентский JSON | block texture | variants |
| minecraft:green_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:green_wool | клиентский JSON | block texture | variants |
| minecraft:grindstone | клиентский JSON | block texture | variants |
| minecraft:hanging_roots | клиентский JSON | block texture | variants |
| minecraft:hay_block | клиентский JSON | block texture | variants |
| minecraft:heavy_core | клиентский JSON | block texture | variants |
| minecraft:heavy_weighted_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:honey_block | клиентский JSON | block texture | variants |
| minecraft:honeycomb_block | клиентский JSON | block texture | variants |
| minecraft:hopper | клиентский JSON | block texture | variants |
| minecraft:horn_coral | клиентский JSON | block texture | variants |
| minecraft:horn_coral_block | клиентский JSON | block texture | variants |
| minecraft:horn_coral_fan | клиентский JSON | block texture | variants |
| minecraft:horn_coral_wall_fan | клиентский JSON | block texture | variants |
| minecraft:ice | клиентский JSON | block texture | variants |
| minecraft:infested_chiseled_stone_bricks | клиентский JSON | block texture | variants |
| minecraft:infested_cobblestone | клиентский JSON | block texture | variants |
| minecraft:infested_cracked_stone_bricks | клиентский JSON | block texture | variants |
| minecraft:infested_deepslate | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:infested_mossy_stone_bricks | клиентский JSON | block texture | variants |
| minecraft:infested_stone | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:infested_stone_bricks | клиентский JSON | block texture | variants |
| minecraft:iron_bars | клиентский JSON | block texture | multipart |
| minecraft:iron_block | клиентский JSON | block texture | variants |
| minecraft:iron_chain | клиентский JSON | block texture | variants |
| minecraft:iron_door | клиентский JSON | block texture | variants |
| minecraft:iron_ore | клиентский JSON | block texture | variants |
| minecraft:iron_trapdoor | клиентский JSON | block texture | variants |
| minecraft:item_frame | клиентский JSON | block texture | variants |
| minecraft:jack_o_lantern | клиентский JSON | block texture | variants |
| minecraft:jigsaw | клиентский JSON | block texture | variants |
| minecraft:jukebox | клиентский JSON | block texture | variants |
| minecraft:jungle_button | клиентский JSON | block texture | variants, uvlock |
| minecraft:jungle_door | клиентский JSON | block texture | variants |
| minecraft:jungle_fence | клиентский JSON | block texture | multipart, uvlock |
| minecraft:jungle_fence_gate | клиентский JSON | block texture | variants, uvlock |
| minecraft:jungle_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:jungle_leaves | клиентский JSON | block texture + явный tint | variants |
| minecraft:jungle_log | клиентский JSON | block texture | variants |
| minecraft:jungle_planks | клиентский JSON | block texture | variants |
| minecraft:jungle_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:jungle_sapling | клиентский JSON | block texture | variants |
| minecraft:jungle_shelf | клиентский JSON | block texture | multipart |
| minecraft:jungle_sign | клиентский JSON | block texture | variants |
| minecraft:jungle_slab | клиентский JSON | block texture | variants |
| minecraft:jungle_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:jungle_trapdoor | клиентский JSON | block texture | variants |
| minecraft:jungle_wall_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:jungle_wall_sign | клиентский JSON | block texture | variants |
| minecraft:jungle_wood | клиентский JSON | block texture | variants |
| minecraft:kelp | клиентский JSON | block texture | variants |
| minecraft:kelp_plant | клиентский JSON | block texture | variants |
| minecraft:ladder | клиентский JSON | block texture | variants |
| minecraft:lantern | клиентский JSON | block texture | variants |
| minecraft:lapis_block | клиентский JSON | block texture | variants |
| minecraft:lapis_ore | клиентский JSON | block texture | variants |
| minecraft:large_amethyst_bud | клиентский JSON | block texture | variants |
| minecraft:large_fern | клиентский JSON | block texture + явный tint | variants |
| minecraft:lava | составная | block texture + цвет | уровень жидкости; статичный кадр течения |
| minecraft:lava_cauldron | клиентский JSON | block texture + явный tint | variants |
| minecraft:leaf_litter | клиентский JSON | block texture + явный tint | multipart |
| minecraft:lectern | клиентский JSON | block texture | variants |
| minecraft:lever | клиентский JSON | block texture | variants |
| minecraft:light | намеренно скрыт | — | воздух/технический блок |
| minecraft:light_blue_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:light_blue_bed | клиентский JSON | block texture | variants |
| minecraft:light_blue_candle | клиентский JSON | block texture | variants |
| minecraft:light_blue_candle_cake | клиентский JSON | block texture | variants |
| minecraft:light_blue_carpet | клиентский JSON | block texture | variants |
| minecraft:light_blue_concrete | клиентский JSON | block texture | variants |
| minecraft:light_blue_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:light_blue_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:light_blue_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:light_blue_stained_glass | клиентский JSON | block texture | variants |
| minecraft:light_blue_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:light_blue_terracotta | клиентский JSON | block texture | variants |
| minecraft:light_blue_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:light_blue_wool | клиентский JSON | block texture | variants |
| minecraft:light_gray_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:light_gray_bed | клиентский JSON | block texture | variants |
| minecraft:light_gray_candle | клиентский JSON | block texture | variants |
| minecraft:light_gray_candle_cake | клиентский JSON | block texture | variants |
| minecraft:light_gray_carpet | клиентский JSON | block texture | variants |
| minecraft:light_gray_concrete | клиентский JSON | block texture | variants |
| minecraft:light_gray_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:light_gray_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:light_gray_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:light_gray_stained_glass | клиентский JSON | block texture | variants |
| minecraft:light_gray_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:light_gray_terracotta | клиентский JSON | block texture | variants |
| minecraft:light_gray_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:light_gray_wool | клиентский JSON | block texture | variants |
| minecraft:light_weighted_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:lightning_rod | клиентский JSON | block texture | variants |
| minecraft:lilac | клиентский JSON | block texture | variants |
| minecraft:lily_of_the_valley | клиентский JSON | block texture | variants |
| minecraft:lily_pad | клиентский JSON | block texture + явный tint | variants, стабильный weighted-вариант |
| minecraft:lime_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:lime_bed | клиентский JSON | block texture | variants |
| minecraft:lime_candle | клиентский JSON | block texture | variants |
| minecraft:lime_candle_cake | клиентский JSON | block texture | variants |
| minecraft:lime_carpet | клиентский JSON | block texture | variants |
| minecraft:lime_concrete | клиентский JSON | block texture | variants |
| minecraft:lime_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:lime_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:lime_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:lime_stained_glass | клиентский JSON | block texture | variants |
| minecraft:lime_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:lime_terracotta | клиентский JSON | block texture | variants |
| minecraft:lime_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:lime_wool | клиентский JSON | block texture | variants |
| minecraft:lodestone | клиентский JSON | block texture | variants |
| minecraft:loom | клиентский JSON | block texture | variants |
| minecraft:magenta_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:magenta_bed | клиентский JSON | block texture | variants |
| minecraft:magenta_candle | клиентский JSON | block texture | variants |
| minecraft:magenta_candle_cake | клиентский JSON | block texture | variants |
| minecraft:magenta_carpet | клиентский JSON | block texture | variants |
| minecraft:magenta_concrete | клиентский JSON | block texture | variants |
| minecraft:magenta_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:magenta_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:magenta_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:magenta_stained_glass | клиентский JSON | block texture | variants |
| minecraft:magenta_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:magenta_terracotta | клиентский JSON | block texture | variants |
| minecraft:magenta_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:magenta_wool | клиентский JSON | block texture | variants |
| minecraft:magma_block | клиентский JSON | block texture | variants |
| minecraft:mangrove_button | клиентский JSON | block texture | variants, uvlock |
| minecraft:mangrove_door | клиентский JSON | block texture | variants |
| minecraft:mangrove_fence | клиентский JSON | block texture | multipart, uvlock |
| minecraft:mangrove_fence_gate | клиентский JSON | block texture | variants, uvlock |
| minecraft:mangrove_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:mangrove_leaves | клиентский JSON | block texture + явный tint | variants |
| minecraft:mangrove_log | клиентский JSON | block texture | variants |
| minecraft:mangrove_planks | клиентский JSON | block texture | variants |
| minecraft:mangrove_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:mangrove_propagule | клиентский JSON | block texture | variants |
| minecraft:mangrove_roots | клиентский JSON | block texture | variants |
| minecraft:mangrove_shelf | клиентский JSON | block texture | multipart |
| minecraft:mangrove_sign | клиентский JSON | block texture | variants |
| minecraft:mangrove_slab | клиентский JSON | block texture | variants |
| minecraft:mangrove_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:mangrove_trapdoor | клиентский JSON | block texture | variants |
| minecraft:mangrove_wall_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:mangrove_wall_sign | клиентский JSON | block texture | variants |
| minecraft:mangrove_wood | клиентский JSON | block texture | variants |
| minecraft:medium_amethyst_bud | клиентский JSON | block texture | variants |
| minecraft:melon | клиентский JSON | block texture | variants |
| minecraft:melon_stem | клиентский JSON | block texture + явный tint | variants |
| minecraft:moss_block | клиентский JSON | block texture | variants |
| minecraft:moss_carpet | клиентский JSON | block texture | variants |
| minecraft:mossy_cobblestone | клиентский JSON | block texture | variants |
| minecraft:mossy_cobblestone_slab | клиентский JSON | block texture | variants |
| minecraft:mossy_cobblestone_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:mossy_cobblestone_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:mossy_stone_brick_slab | клиентский JSON | block texture | variants |
| minecraft:mossy_stone_brick_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:mossy_stone_brick_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:mossy_stone_bricks | клиентский JSON | block texture | variants |
| minecraft:moving_piston | намеренно скрыт | — | воздух/технический блок |
| minecraft:mud | клиентский JSON | block texture | variants |
| minecraft:mud_brick_slab | клиентский JSON | block texture | variants |
| minecraft:mud_brick_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:mud_brick_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:mud_bricks | клиентский JSON | block texture | variants |
| minecraft:muddy_mangrove_roots | клиентский JSON | block texture | variants |
| minecraft:mushroom_stem | клиентский JSON | block texture | multipart, uvlock |
| minecraft:mycelium | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:nether_brick_fence | клиентский JSON | block texture | multipart, uvlock |
| minecraft:nether_brick_slab | клиентский JSON | block texture | variants |
| minecraft:nether_brick_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:nether_brick_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:nether_bricks | клиентский JSON | block texture | variants |
| minecraft:nether_gold_ore | клиентский JSON | block texture | variants |
| minecraft:nether_portal | клиентский JSON | block texture | variants |
| minecraft:nether_quartz_ore | клиентский JSON | block texture | variants |
| minecraft:nether_sprouts | клиентский JSON | block texture | variants |
| minecraft:nether_wart | клиентский JSON | block texture | variants |
| minecraft:nether_wart_block | клиентский JSON | block texture | variants |
| minecraft:netherite_block | клиентский JSON | block texture | variants |
| minecraft:netherrack | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:note_block | клиентский JSON | block texture | variants |
| minecraft:oak_button | клиентский JSON | block texture | variants, uvlock |
| minecraft:oak_door | клиентский JSON | block texture | variants |
| minecraft:oak_fence | клиентский JSON | block texture | multipart, uvlock |
| minecraft:oak_fence_gate | клиентский JSON | block texture | variants, uvlock |
| minecraft:oak_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:oak_leaves | клиентский JSON | block texture + явный tint | variants |
| minecraft:oak_log | клиентский JSON | block texture | variants |
| minecraft:oak_planks | клиентский JSON | block texture | variants |
| minecraft:oak_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:oak_sapling | клиентский JSON | block texture | variants |
| minecraft:oak_shelf | клиентский JSON | block texture | multipart |
| minecraft:oak_sign | клиентский JSON | block texture | variants |
| minecraft:oak_slab | клиентский JSON | block texture | variants |
| minecraft:oak_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:oak_trapdoor | клиентский JSON | block texture | variants |
| minecraft:oak_wall_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:oak_wall_sign | клиентский JSON | block texture | variants |
| minecraft:oak_wood | клиентский JSON | block texture | variants |
| minecraft:observer | клиентский JSON | block texture | variants |
| minecraft:obsidian | клиентский JSON | block texture | variants |
| minecraft:ochre_froglight | клиентский JSON | block texture | variants |
| minecraft:open_eyeblossom | клиентский JSON | block texture | variants |
| minecraft:orange_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:orange_bed | клиентский JSON | block texture | variants |
| minecraft:orange_candle | клиентский JSON | block texture | variants |
| minecraft:orange_candle_cake | клиентский JSON | block texture | variants |
| minecraft:orange_carpet | клиентский JSON | block texture | variants |
| minecraft:orange_concrete | клиентский JSON | block texture | variants |
| minecraft:orange_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:orange_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:orange_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:orange_stained_glass | клиентский JSON | block texture | variants |
| minecraft:orange_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:orange_terracotta | клиентский JSON | block texture | variants |
| minecraft:orange_tulip | клиентский JSON | block texture | variants |
| minecraft:orange_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:orange_wool | клиентский JSON | block texture | variants |
| minecraft:oxeye_daisy | клиентский JSON | block texture | variants |
| minecraft:oxidized_chiseled_copper | клиентский JSON | block texture | variants |
| minecraft:oxidized_copper | клиентский JSON | block texture | variants |
| minecraft:oxidized_copper_bars | клиентский JSON | block texture | multipart |
| minecraft:oxidized_copper_bulb | клиентский JSON | block texture | variants |
| minecraft:oxidized_copper_chain | клиентский JSON | block texture | variants |
| minecraft:oxidized_copper_chest | составная | entity/effect texture | тип, направление и стадия меди |
| minecraft:oxidized_copper_door | клиентский JSON | block texture | variants |
| minecraft:oxidized_copper_golem_statue | составная | entity/effect texture | составная статуя и стадия окисления |
| minecraft:oxidized_copper_grate | клиентский JSON | block texture | variants |
| minecraft:oxidized_copper_lantern | клиентский JSON | block texture | variants |
| minecraft:oxidized_copper_trapdoor | клиентский JSON | block texture | variants |
| minecraft:oxidized_cut_copper | клиентский JSON | block texture | variants |
| minecraft:oxidized_cut_copper_slab | клиентский JSON | block texture | variants |
| minecraft:oxidized_cut_copper_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:oxidized_lightning_rod | клиентский JSON | block texture | variants |
| minecraft:packed_ice | клиентский JSON | block texture | variants |
| minecraft:packed_mud | клиентский JSON | block texture | variants |
| minecraft:pale_hanging_moss | клиентский JSON | block texture | variants |
| minecraft:pale_moss_block | клиентский JSON | block texture | variants |
| minecraft:pale_moss_carpet | клиентский JSON | block texture | multipart, uvlock |
| minecraft:pale_oak_button | клиентский JSON | block texture | variants, uvlock |
| minecraft:pale_oak_door | клиентский JSON | block texture | variants |
| minecraft:pale_oak_fence | клиентский JSON | block texture | multipart, uvlock |
| minecraft:pale_oak_fence_gate | клиентский JSON | block texture | variants, uvlock |
| minecraft:pale_oak_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:pale_oak_leaves | клиентский JSON | block texture + явный tint | variants |
| minecraft:pale_oak_log | клиентский JSON | block texture | variants |
| minecraft:pale_oak_planks | клиентский JSON | block texture | variants |
| minecraft:pale_oak_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:pale_oak_sapling | клиентский JSON | block texture | variants |
| minecraft:pale_oak_shelf | клиентский JSON | block texture | multipart |
| minecraft:pale_oak_sign | клиентский JSON | block texture | variants |
| minecraft:pale_oak_slab | клиентский JSON | block texture | variants |
| minecraft:pale_oak_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:pale_oak_trapdoor | клиентский JSON | block texture | variants |
| minecraft:pale_oak_wall_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:pale_oak_wall_sign | клиентский JSON | block texture | variants |
| minecraft:pale_oak_wood | клиентский JSON | block texture | variants |
| minecraft:pearlescent_froglight | клиентский JSON | block texture | variants |
| minecraft:peony | клиентский JSON | block texture | variants |
| minecraft:petrified_oak_slab | клиентский JSON | block texture | variants |
| minecraft:piglin_head | составная | entity/effect texture | моб-скин; player profile использует Steve |
| minecraft:piglin_wall_head | составная | entity/effect texture | моб-скин; player profile использует Steve |
| minecraft:pink_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:pink_bed | клиентский JSON | block texture | variants |
| minecraft:pink_candle | клиентский JSON | block texture | variants |
| minecraft:pink_candle_cake | клиентский JSON | block texture | variants |
| minecraft:pink_carpet | клиентский JSON | block texture | variants |
| minecraft:pink_concrete | клиентский JSON | block texture | variants |
| minecraft:pink_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:pink_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:pink_petals | клиентский JSON | block texture + явный tint | multipart |
| minecraft:pink_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:pink_stained_glass | клиентский JSON | block texture | variants |
| minecraft:pink_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:pink_terracotta | клиентский JSON | block texture | variants |
| minecraft:pink_tulip | клиентский JSON | block texture | variants |
| minecraft:pink_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:pink_wool | клиентский JSON | block texture | variants |
| minecraft:piston | клиентский JSON | block texture | variants |
| minecraft:piston_head | клиентский JSON | block texture | variants |
| minecraft:pitcher_crop | JSON | block texture | пустая верхняя часть ранних стадий штатна |
| minecraft:pitcher_plant | клиентский JSON | block texture | variants |
| minecraft:player_head | составная | entity/effect texture | моб-скин; player profile использует Steve |
| minecraft:player_wall_head | составная | entity/effect texture | моб-скин; player profile использует Steve |
| minecraft:podzol | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:pointed_dripstone | клиентский JSON | block texture | variants |
| minecraft:polished_andesite | клиентский JSON | block texture | variants |
| minecraft:polished_andesite_slab | клиентский JSON | block texture | variants |
| minecraft:polished_andesite_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:polished_basalt | клиентский JSON | block texture | variants |
| minecraft:polished_blackstone | клиентский JSON | block texture | variants |
| minecraft:polished_blackstone_brick_slab | клиентский JSON | block texture | variants |
| minecraft:polished_blackstone_brick_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:polished_blackstone_brick_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:polished_blackstone_bricks | клиентский JSON | block texture | variants |
| minecraft:polished_blackstone_button | клиентский JSON | block texture | variants, uvlock |
| minecraft:polished_blackstone_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:polished_blackstone_slab | клиентский JSON | block texture | variants |
| minecraft:polished_blackstone_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:polished_blackstone_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:polished_cinnabar | клиентский JSON | block texture | variants |
| minecraft:polished_cinnabar_slab | клиентский JSON | block texture | variants |
| minecraft:polished_cinnabar_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:polished_cinnabar_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:polished_deepslate | клиентский JSON | block texture | variants |
| minecraft:polished_deepslate_slab | клиентский JSON | block texture | variants |
| minecraft:polished_deepslate_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:polished_deepslate_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:polished_diorite | клиентский JSON | block texture | variants |
| minecraft:polished_diorite_slab | клиентский JSON | block texture | variants |
| minecraft:polished_diorite_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:polished_granite | клиентский JSON | block texture | variants |
| minecraft:polished_granite_slab | клиентский JSON | block texture | variants |
| minecraft:polished_granite_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:polished_sulfur | клиентский JSON | block texture | variants |
| minecraft:polished_sulfur_slab | клиентский JSON | block texture | variants |
| minecraft:polished_sulfur_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:polished_sulfur_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:polished_tuff | клиентский JSON | block texture | variants |
| minecraft:polished_tuff_slab | клиентский JSON | block texture | variants |
| minecraft:polished_tuff_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:polished_tuff_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:poppy | клиентский JSON | block texture | variants |
| minecraft:potatoes | клиентский JSON | block texture | variants |
| minecraft:potent_sulfur | клиентский JSON | block texture | variants |
| minecraft:potted_acacia_sapling | клиентский JSON | block texture | variants |
| minecraft:potted_allium | клиентский JSON | block texture | variants |
| minecraft:potted_azalea_bush | клиентский JSON | block texture | variants |
| minecraft:potted_azure_bluet | клиентский JSON | block texture | variants |
| minecraft:potted_bamboo | клиентский JSON | block texture | variants |
| minecraft:potted_birch_sapling | клиентский JSON | block texture | variants |
| minecraft:potted_blue_orchid | клиентский JSON | block texture | variants |
| minecraft:potted_brown_mushroom | клиентский JSON | block texture | variants |
| minecraft:potted_cactus | клиентский JSON | block texture | variants |
| minecraft:potted_cherry_sapling | клиентский JSON | block texture | variants |
| minecraft:potted_closed_eyeblossom | клиентский JSON | block texture | variants |
| minecraft:potted_cornflower | клиентский JSON | block texture | variants |
| minecraft:potted_crimson_fungus | клиентский JSON | block texture | variants |
| minecraft:potted_crimson_roots | клиентский JSON | block texture | variants |
| minecraft:potted_dandelion | клиентский JSON | block texture | variants |
| minecraft:potted_dark_oak_sapling | клиентский JSON | block texture | variants |
| minecraft:potted_dead_bush | клиентский JSON | block texture | variants |
| minecraft:potted_fern | клиентский JSON | block texture + явный tint | variants |
| minecraft:potted_flowering_azalea_bush | клиентский JSON | block texture | variants |
| minecraft:potted_golden_dandelion | клиентский JSON | block texture | variants |
| minecraft:potted_jungle_sapling | клиентский JSON | block texture | variants |
| minecraft:potted_lily_of_the_valley | клиентский JSON | block texture | variants |
| minecraft:potted_mangrove_propagule | клиентский JSON | block texture | variants |
| minecraft:potted_oak_sapling | клиентский JSON | block texture | variants |
| minecraft:potted_open_eyeblossom | клиентский JSON | block texture | variants |
| minecraft:potted_orange_tulip | клиентский JSON | block texture | variants |
| minecraft:potted_oxeye_daisy | клиентский JSON | block texture | variants |
| minecraft:potted_pale_oak_sapling | клиентский JSON | block texture | variants |
| minecraft:potted_pink_tulip | клиентский JSON | block texture | variants |
| minecraft:potted_poppy | клиентский JSON | block texture | variants |
| minecraft:potted_red_mushroom | клиентский JSON | block texture | variants |
| minecraft:potted_red_tulip | клиентский JSON | block texture | variants |
| minecraft:potted_spruce_sapling | клиентский JSON | block texture | variants |
| minecraft:potted_torchflower | клиентский JSON | block texture | variants |
| minecraft:potted_warped_fungus | клиентский JSON | block texture | variants |
| minecraft:potted_warped_roots | клиентский JSON | block texture | variants |
| minecraft:potted_white_tulip | клиентский JSON | block texture | variants |
| minecraft:potted_wither_rose | клиентский JSON | block texture | variants |
| minecraft:powder_snow | клиентский JSON | block texture | variants |
| minecraft:powder_snow_cauldron | клиентский JSON | block texture + явный tint | variants |
| minecraft:powered_rail | клиентский JSON | block texture | variants |
| minecraft:prismarine | клиентский JSON | block texture | variants |
| minecraft:prismarine_brick_slab | клиентский JSON | block texture | variants |
| minecraft:prismarine_brick_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:prismarine_bricks | клиентский JSON | block texture | variants |
| minecraft:prismarine_slab | клиентский JSON | block texture | variants |
| minecraft:prismarine_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:prismarine_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:pumpkin | клиентский JSON | block texture | variants |
| minecraft:pumpkin_stem | клиентский JSON | block texture + явный tint | variants |
| minecraft:purple_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:purple_bed | клиентский JSON | block texture | variants |
| minecraft:purple_candle | клиентский JSON | block texture | variants |
| minecraft:purple_candle_cake | клиентский JSON | block texture | variants |
| minecraft:purple_carpet | клиентский JSON | block texture | variants |
| minecraft:purple_concrete | клиентский JSON | block texture | variants |
| minecraft:purple_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:purple_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:purple_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:purple_stained_glass | клиентский JSON | block texture | variants |
| minecraft:purple_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:purple_terracotta | клиентский JSON | block texture | variants |
| minecraft:purple_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:purple_wool | клиентский JSON | block texture | variants |
| minecraft:purpur_block | клиентский JSON | block texture | variants |
| minecraft:purpur_pillar | клиентский JSON | block texture | variants |
| minecraft:purpur_slab | клиентский JSON | block texture | variants |
| minecraft:purpur_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:quartz_block | клиентский JSON | block texture | variants |
| minecraft:quartz_bricks | клиентский JSON | block texture | variants |
| minecraft:quartz_pillar | клиентский JSON | block texture | variants |
| minecraft:quartz_slab | клиентский JSON | block texture | variants |
| minecraft:quartz_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:rail | клиентский JSON | block texture | variants |
| minecraft:raw_copper_block | клиентский JSON | block texture | variants |
| minecraft:raw_gold_block | клиентский JSON | block texture | variants |
| minecraft:raw_iron_block | клиентский JSON | block texture | variants |
| minecraft:red_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:red_bed | клиентский JSON | block texture | variants |
| minecraft:red_candle | клиентский JSON | block texture | variants |
| minecraft:red_candle_cake | клиентский JSON | block texture | variants |
| minecraft:red_carpet | клиентский JSON | block texture | variants |
| minecraft:red_concrete | клиентский JSON | block texture | variants |
| minecraft:red_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:red_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:red_mushroom | клиентский JSON | block texture | variants |
| minecraft:red_mushroom_block | клиентский JSON | block texture | multipart, uvlock |
| minecraft:red_nether_brick_slab | клиентский JSON | block texture | variants |
| minecraft:red_nether_brick_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:red_nether_brick_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:red_nether_bricks | клиентский JSON | block texture | variants |
| minecraft:red_sand | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:red_sandstone | клиентский JSON | block texture | variants |
| minecraft:red_sandstone_slab | клиентский JSON | block texture | variants |
| minecraft:red_sandstone_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:red_sandstone_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:red_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:red_stained_glass | клиентский JSON | block texture | variants |
| minecraft:red_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:red_terracotta | клиентский JSON | block texture | variants |
| minecraft:red_tulip | клиентский JSON | block texture | variants |
| minecraft:red_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:red_wool | клиентский JSON | block texture | variants |
| minecraft:redstone_block | клиентский JSON | block texture | variants |
| minecraft:redstone_lamp | клиентский JSON | block texture | variants |
| minecraft:redstone_ore | клиентский JSON | block texture | variants |
| minecraft:redstone_torch | клиентский JSON | block texture | variants |
| minecraft:redstone_wall_torch | клиентский JSON | block texture | variants |
| minecraft:redstone_wire | клиентский JSON | block texture + явный tint | multipart |
| minecraft:reinforced_deepslate | клиентский JSON | block texture | variants |
| minecraft:repeater | клиентский JSON | block texture | variants |
| minecraft:repeating_command_block | клиентский JSON | block texture | variants |
| minecraft:resin_block | клиентский JSON | block texture | variants |
| minecraft:resin_brick_slab | клиентский JSON | block texture | variants |
| minecraft:resin_brick_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:resin_brick_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:resin_bricks | клиентский JSON | block texture | variants |
| minecraft:resin_clump | клиентский JSON | block texture | multipart, uvlock |
| minecraft:respawn_anchor | клиентский JSON | block texture | variants |
| minecraft:rooted_dirt | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:rose_bush | клиентский JSON | block texture | variants |
| minecraft:sand | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:sandstone | клиентский JSON | block texture | variants |
| minecraft:sandstone_slab | клиентский JSON | block texture | variants |
| minecraft:sandstone_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:sandstone_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:scaffolding | клиентский JSON | block texture | variants |
| minecraft:sculk | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:sculk_catalyst | клиентский JSON | block texture | variants |
| minecraft:sculk_sensor | клиентский JSON | block texture | variants |
| minecraft:sculk_shrieker | клиентский JSON | block texture | variants |
| minecraft:sculk_vein | клиентский JSON | block texture | multipart, uvlock |
| minecraft:sea_lantern | клиентский JSON | block texture | variants |
| minecraft:sea_pickle | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:seagrass | клиентский JSON | block texture | variants |
| minecraft:short_dry_grass | клиентский JSON | block texture | variants |
| minecraft:short_grass | клиентский JSON | block texture + явный tint | variants |
| minecraft:shroomlight | клиентский JSON | block texture | variants |
| minecraft:shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:skeleton_skull | составная | entity/effect texture | моб-скин; player profile использует Steve |
| minecraft:skeleton_wall_skull | составная | entity/effect texture | моб-скин; player profile использует Steve |
| minecraft:slime_block | клиентский JSON | block texture | variants |
| minecraft:small_amethyst_bud | клиентский JSON | block texture | variants |
| minecraft:small_dripleaf | клиентский JSON | block texture | variants |
| minecraft:smithing_table | клиентский JSON | block texture | variants |
| minecraft:smoker | клиентский JSON | block texture | variants |
| minecraft:smooth_basalt | клиентский JSON | block texture | variants |
| minecraft:smooth_quartz | клиентский JSON | block texture | variants |
| minecraft:smooth_quartz_slab | клиентский JSON | block texture | variants |
| minecraft:smooth_quartz_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:smooth_red_sandstone | клиентский JSON | block texture | variants |
| minecraft:smooth_red_sandstone_slab | клиентский JSON | block texture | variants |
| minecraft:smooth_red_sandstone_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:smooth_sandstone | клиентский JSON | block texture | variants |
| minecraft:smooth_sandstone_slab | клиентский JSON | block texture | variants |
| minecraft:smooth_sandstone_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:smooth_stone | клиентский JSON | block texture | variants |
| minecraft:smooth_stone_slab | клиентский JSON | block texture | variants |
| minecraft:sniffer_egg | клиентский JSON | block texture | variants |
| minecraft:snow | клиентский JSON | block texture | variants |
| minecraft:snow_block | клиентский JSON | block texture | variants |
| minecraft:soul_campfire | клиентский JSON | block texture | variants |
| minecraft:soul_fire | клиентский JSON | block texture | multipart |
| minecraft:soul_lantern | клиентский JSON | block texture | variants |
| minecraft:soul_sand | клиентский JSON | block texture | variants |
| minecraft:soul_soil | клиентский JSON | block texture | variants |
| minecraft:soul_torch | клиентский JSON | block texture | variants |
| minecraft:soul_wall_torch | клиентский JSON | block texture | variants |
| minecraft:spawner | клиентский JSON | block texture | variants |
| minecraft:sponge | клиентский JSON | block texture | variants |
| minecraft:spore_blossom | клиентский JSON | block texture | variants |
| minecraft:spruce_button | клиентский JSON | block texture | variants, uvlock |
| minecraft:spruce_door | клиентский JSON | block texture | variants |
| minecraft:spruce_fence | клиентский JSON | block texture | multipart, uvlock |
| minecraft:spruce_fence_gate | клиентский JSON | block texture | variants, uvlock |
| minecraft:spruce_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:spruce_leaves | клиентский JSON | block texture + явный tint | variants |
| minecraft:spruce_log | клиентский JSON | block texture | variants |
| minecraft:spruce_planks | клиентский JSON | block texture | variants |
| minecraft:spruce_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:spruce_sapling | клиентский JSON | block texture | variants |
| minecraft:spruce_shelf | клиентский JSON | block texture | multipart |
| minecraft:spruce_sign | клиентский JSON | block texture | variants |
| minecraft:spruce_slab | клиентский JSON | block texture | variants |
| minecraft:spruce_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:spruce_trapdoor | клиентский JSON | block texture | variants |
| minecraft:spruce_wall_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:spruce_wall_sign | клиентский JSON | block texture | variants |
| minecraft:spruce_wood | клиентский JSON | block texture | variants |
| minecraft:sticky_piston | клиентский JSON | block texture | variants |
| minecraft:stone | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:stone_brick_slab | клиентский JSON | block texture | variants |
| minecraft:stone_brick_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:stone_brick_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:stone_bricks | клиентский JSON | block texture | variants |
| minecraft:stone_button | клиентский JSON | block texture | variants, uvlock |
| minecraft:stone_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:stone_slab | клиентский JSON | block texture | variants |
| minecraft:stone_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:stonecutter | клиентский JSON | block texture + явный tint | variants |
| minecraft:stripped_acacia_log | клиентский JSON | block texture | variants |
| minecraft:stripped_acacia_wood | клиентский JSON | block texture | variants |
| minecraft:stripped_bamboo_block | клиентский JSON | block texture | variants |
| minecraft:stripped_birch_log | клиентский JSON | block texture | variants |
| minecraft:stripped_birch_wood | клиентский JSON | block texture | variants |
| minecraft:stripped_cherry_log | клиентский JSON | block texture | variants |
| minecraft:stripped_cherry_wood | клиентский JSON | block texture | variants |
| minecraft:stripped_crimson_hyphae | клиентский JSON | block texture | variants |
| minecraft:stripped_crimson_stem | клиентский JSON | block texture | variants |
| minecraft:stripped_dark_oak_log | клиентский JSON | block texture | variants |
| minecraft:stripped_dark_oak_wood | клиентский JSON | block texture | variants |
| minecraft:stripped_jungle_log | клиентский JSON | block texture | variants |
| minecraft:stripped_jungle_wood | клиентский JSON | block texture | variants |
| minecraft:stripped_mangrove_log | клиентский JSON | block texture | variants |
| minecraft:stripped_mangrove_wood | клиентский JSON | block texture | variants |
| minecraft:stripped_oak_log | клиентский JSON | block texture | variants |
| minecraft:stripped_oak_wood | клиентский JSON | block texture | variants |
| minecraft:stripped_pale_oak_log | клиентский JSON | block texture | variants |
| minecraft:stripped_pale_oak_wood | клиентский JSON | block texture | variants |
| minecraft:stripped_spruce_log | клиентский JSON | block texture | variants |
| minecraft:stripped_spruce_wood | клиентский JSON | block texture | variants |
| minecraft:stripped_warped_hyphae | клиентский JSON | block texture | variants |
| minecraft:stripped_warped_stem | клиентский JSON | block texture | variants |
| minecraft:structure_block | клиентский JSON | block texture | variants |
| minecraft:structure_void | намеренно скрыт | — | воздух/технический блок |
| minecraft:sugar_cane | клиентский JSON | block texture + явный tint | variants |
| minecraft:sulfur | клиентский JSON | block texture | variants |
| minecraft:sulfur_brick_slab | клиентский JSON | block texture | variants |
| minecraft:sulfur_brick_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:sulfur_brick_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:sulfur_bricks | клиентский JSON | block texture | variants |
| minecraft:sulfur_slab | клиентский JSON | block texture | variants |
| minecraft:sulfur_spike | клиентский JSON | block texture | variants |
| minecraft:sulfur_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:sulfur_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:sunflower | клиентский JSON | block texture | variants |
| minecraft:suspicious_gravel | клиентский JSON | block texture | variants |
| minecraft:suspicious_sand | клиентский JSON | block texture | variants |
| minecraft:sweet_berry_bush | клиентский JSON | block texture | variants |
| minecraft:tall_dry_grass | клиентский JSON | block texture | variants |
| minecraft:tall_grass | клиентский JSON | block texture + явный tint | variants |
| minecraft:tall_seagrass | клиентский JSON | block texture | variants |
| minecraft:target | клиентский JSON | block texture | variants |
| minecraft:terracotta | клиентский JSON | block texture | variants |
| minecraft:test_block | клиентский JSON | block texture | variants |
| minecraft:test_instance_block | клиентский JSON | block texture | variants |
| minecraft:tinted_glass | клиентский JSON | block texture | variants |
| minecraft:tnt | клиентский JSON | block texture | variants |
| minecraft:torch | клиентский JSON | block texture | variants |
| minecraft:torchflower | клиентский JSON | block texture | variants |
| minecraft:torchflower_crop | клиентский JSON | block texture | variants |
| minecraft:trapped_chest | составная | entity/effect texture | тип, направление и стадия меди |
| minecraft:trial_spawner | клиентский JSON | block texture | variants |
| minecraft:tripwire | клиентский JSON | block texture | variants |
| minecraft:tripwire_hook | клиентский JSON | block texture | variants |
| minecraft:tube_coral | клиентский JSON | block texture | variants |
| minecraft:tube_coral_block | клиентский JSON | block texture | variants |
| minecraft:tube_coral_fan | клиентский JSON | block texture | variants |
| minecraft:tube_coral_wall_fan | клиентский JSON | block texture | variants |
| minecraft:tuff | клиентский JSON | block texture | variants |
| minecraft:tuff_brick_slab | клиентский JSON | block texture | variants |
| minecraft:tuff_brick_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:tuff_brick_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:tuff_bricks | клиентский JSON | block texture | variants |
| minecraft:tuff_slab | клиентский JSON | block texture | variants |
| minecraft:tuff_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:tuff_wall | клиентский JSON | block texture | multipart, uvlock |
| minecraft:turtle_egg | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:twisting_vines | клиентский JSON | block texture | variants |
| minecraft:twisting_vines_plant | клиентский JSON | block texture | variants |
| minecraft:vault | клиентский JSON | block texture | variants |
| minecraft:verdant_froglight | клиентский JSON | block texture | variants |
| minecraft:vine | клиентский JSON | block texture + явный tint | multipart, uvlock |
| minecraft:void_air | намеренно скрыт | — | воздух/технический блок |
| minecraft:wall_torch | клиентский JSON | block texture | variants |
| minecraft:warped_button | клиентский JSON | block texture | variants, uvlock |
| minecraft:warped_door | клиентский JSON | block texture | variants |
| minecraft:warped_fence | клиентский JSON | block texture | multipart, uvlock |
| minecraft:warped_fence_gate | клиентский JSON | block texture | variants, uvlock |
| minecraft:warped_fungus | клиентский JSON | block texture | variants |
| minecraft:warped_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:warped_hyphae | клиентский JSON | block texture | variants |
| minecraft:warped_nylium | клиентский JSON | block texture | variants |
| minecraft:warped_planks | клиентский JSON | block texture | variants |
| minecraft:warped_pressure_plate | клиентский JSON | block texture | variants |
| minecraft:warped_roots | клиентский JSON | block texture | variants |
| minecraft:warped_shelf | клиентский JSON | block texture | multipart |
| minecraft:warped_sign | клиентский JSON | block texture | variants |
| minecraft:warped_slab | клиентский JSON | block texture | variants |
| minecraft:warped_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:warped_stem | клиентский JSON | block texture | variants |
| minecraft:warped_trapdoor | клиентский JSON | block texture | variants |
| minecraft:warped_wall_hanging_sign | клиентский JSON | block texture | variants |
| minecraft:warped_wall_sign | клиентский JSON | block texture | variants |
| minecraft:warped_wart_block | клиентский JSON | block texture | variants |
| minecraft:water | составная | block texture + цвет | уровень жидкости; статичный кадр течения |
| minecraft:water_cauldron | клиентский JSON | block texture + явный tint | variants |
| minecraft:waxed_chiseled_copper | клиентский JSON | block texture | variants |
| minecraft:waxed_copper_bars | клиентский JSON | block texture | multipart |
| minecraft:waxed_copper_block | клиентский JSON | block texture | variants |
| minecraft:waxed_copper_bulb | клиентский JSON | block texture | variants |
| minecraft:waxed_copper_chain | клиентский JSON | block texture | variants |
| minecraft:waxed_copper_chest | составная | entity/effect texture | тип, направление и стадия меди |
| minecraft:waxed_copper_door | клиентский JSON | block texture | variants |
| minecraft:waxed_copper_golem_statue | составная | entity/effect texture | составная статуя и стадия окисления |
| minecraft:waxed_copper_grate | клиентский JSON | block texture | variants |
| minecraft:waxed_copper_lantern | клиентский JSON | block texture | variants |
| minecraft:waxed_copper_trapdoor | клиентский JSON | block texture | variants |
| minecraft:waxed_cut_copper | клиентский JSON | block texture | variants |
| minecraft:waxed_cut_copper_slab | клиентский JSON | block texture | variants |
| minecraft:waxed_cut_copper_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:waxed_exposed_chiseled_copper | клиентский JSON | block texture | variants |
| minecraft:waxed_exposed_copper | клиентский JSON | block texture | variants |
| minecraft:waxed_exposed_copper_bars | клиентский JSON | block texture | multipart |
| minecraft:waxed_exposed_copper_bulb | клиентский JSON | block texture | variants |
| minecraft:waxed_exposed_copper_chain | клиентский JSON | block texture | variants |
| minecraft:waxed_exposed_copper_chest | составная | entity/effect texture | тип, направление и стадия меди |
| minecraft:waxed_exposed_copper_door | клиентский JSON | block texture | variants |
| minecraft:waxed_exposed_copper_golem_statue | составная | entity/effect texture | составная статуя и стадия окисления |
| minecraft:waxed_exposed_copper_grate | клиентский JSON | block texture | variants |
| minecraft:waxed_exposed_copper_lantern | клиентский JSON | block texture | variants |
| minecraft:waxed_exposed_copper_trapdoor | клиентский JSON | block texture | variants |
| minecraft:waxed_exposed_cut_copper | клиентский JSON | block texture | variants |
| minecraft:waxed_exposed_cut_copper_slab | клиентский JSON | block texture | variants |
| minecraft:waxed_exposed_cut_copper_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:waxed_exposed_lightning_rod | клиентский JSON | block texture | variants |
| minecraft:waxed_lightning_rod | клиентский JSON | block texture | variants |
| minecraft:waxed_oxidized_chiseled_copper | клиентский JSON | block texture | variants |
| minecraft:waxed_oxidized_copper | клиентский JSON | block texture | variants |
| minecraft:waxed_oxidized_copper_bars | клиентский JSON | block texture | multipart |
| minecraft:waxed_oxidized_copper_bulb | клиентский JSON | block texture | variants |
| minecraft:waxed_oxidized_copper_chain | клиентский JSON | block texture | variants |
| minecraft:waxed_oxidized_copper_chest | составная | entity/effect texture | тип, направление и стадия меди |
| minecraft:waxed_oxidized_copper_door | клиентский JSON | block texture | variants |
| minecraft:waxed_oxidized_copper_golem_statue | составная | entity/effect texture | составная статуя и стадия окисления |
| minecraft:waxed_oxidized_copper_grate | клиентский JSON | block texture | variants |
| minecraft:waxed_oxidized_copper_lantern | клиентский JSON | block texture | variants |
| minecraft:waxed_oxidized_copper_trapdoor | клиентский JSON | block texture | variants |
| minecraft:waxed_oxidized_cut_copper | клиентский JSON | block texture | variants |
| minecraft:waxed_oxidized_cut_copper_slab | клиентский JSON | block texture | variants |
| minecraft:waxed_oxidized_cut_copper_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:waxed_oxidized_lightning_rod | клиентский JSON | block texture | variants |
| minecraft:waxed_weathered_chiseled_copper | клиентский JSON | block texture | variants |
| minecraft:waxed_weathered_copper | клиентский JSON | block texture | variants |
| minecraft:waxed_weathered_copper_bars | клиентский JSON | block texture | multipart |
| minecraft:waxed_weathered_copper_bulb | клиентский JSON | block texture | variants |
| minecraft:waxed_weathered_copper_chain | клиентский JSON | block texture | variants |
| minecraft:waxed_weathered_copper_chest | составная | entity/effect texture | тип, направление и стадия меди |
| minecraft:waxed_weathered_copper_door | клиентский JSON | block texture | variants |
| minecraft:waxed_weathered_copper_golem_statue | составная | entity/effect texture | составная статуя и стадия окисления |
| minecraft:waxed_weathered_copper_grate | клиентский JSON | block texture | variants |
| minecraft:waxed_weathered_copper_lantern | клиентский JSON | block texture | variants |
| minecraft:waxed_weathered_copper_trapdoor | клиентский JSON | block texture | variants |
| minecraft:waxed_weathered_cut_copper | клиентский JSON | block texture | variants |
| minecraft:waxed_weathered_cut_copper_slab | клиентский JSON | block texture | variants |
| minecraft:waxed_weathered_cut_copper_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:waxed_weathered_lightning_rod | клиентский JSON | block texture | variants |
| minecraft:weathered_chiseled_copper | клиентский JSON | block texture | variants |
| minecraft:weathered_copper | клиентский JSON | block texture | variants |
| minecraft:weathered_copper_bars | клиентский JSON | block texture | multipart |
| minecraft:weathered_copper_bulb | клиентский JSON | block texture | variants |
| minecraft:weathered_copper_chain | клиентский JSON | block texture | variants |
| minecraft:weathered_copper_chest | составная | entity/effect texture | тип, направление и стадия меди |
| minecraft:weathered_copper_door | клиентский JSON | block texture | variants |
| minecraft:weathered_copper_golem_statue | составная | entity/effect texture | составная статуя и стадия окисления |
| minecraft:weathered_copper_grate | клиентский JSON | block texture | variants |
| minecraft:weathered_copper_lantern | клиентский JSON | block texture | variants |
| minecraft:weathered_copper_trapdoor | клиентский JSON | block texture | variants |
| minecraft:weathered_cut_copper | клиентский JSON | block texture | variants |
| minecraft:weathered_cut_copper_slab | клиентский JSON | block texture | variants |
| minecraft:weathered_cut_copper_stairs | клиентский JSON | block texture | variants, uvlock |
| minecraft:weathered_lightning_rod | клиентский JSON | block texture | variants |
| minecraft:weeping_vines | клиентский JSON | block texture | variants |
| minecraft:weeping_vines_plant | клиентский JSON | block texture | variants |
| minecraft:wet_sponge | клиентский JSON | block texture | variants |
| minecraft:wheat | клиентский JSON | block texture | variants |
| minecraft:white_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:white_bed | клиентский JSON | block texture | variants |
| minecraft:white_candle | клиентский JSON | block texture | variants |
| minecraft:white_candle_cake | клиентский JSON | block texture | variants |
| minecraft:white_carpet | клиентский JSON | block texture | variants |
| minecraft:white_concrete | клиентский JSON | block texture | variants |
| minecraft:white_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:white_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:white_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:white_stained_glass | клиентский JSON | block texture | variants |
| minecraft:white_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:white_terracotta | клиентский JSON | block texture | variants |
| minecraft:white_tulip | клиентский JSON | block texture | variants |
| minecraft:white_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:white_wool | клиентский JSON | block texture | variants |
| minecraft:wildflowers | клиентский JSON | block texture + явный tint | multipart |
| minecraft:wither_rose | клиентский JSON | block texture | variants |
| minecraft:wither_skeleton_skull | составная | entity/effect texture | моб-скин; player profile использует Steve |
| minecraft:wither_skeleton_wall_skull | составная | entity/effect texture | моб-скин; player profile использует Steve |
| minecraft:yellow_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:yellow_bed | клиентский JSON | block texture | variants |
| minecraft:yellow_candle | клиентский JSON | block texture | variants |
| minecraft:yellow_candle_cake | клиентский JSON | block texture | variants |
| minecraft:yellow_carpet | клиентский JSON | block texture | variants |
| minecraft:yellow_concrete | клиентский JSON | block texture | variants |
| minecraft:yellow_concrete_powder | клиентский JSON | block texture | variants, стабильный weighted-вариант |
| minecraft:yellow_glazed_terracotta | клиентский JSON | block texture | variants |
| minecraft:yellow_shulker_box | составная | entity/effect texture | закрытая коробка из основания и крышки |
| minecraft:yellow_stained_glass | клиентский JSON | block texture | variants |
| minecraft:yellow_stained_glass_pane | клиентский JSON | block texture | multipart |
| minecraft:yellow_terracotta | клиентский JSON | block texture | variants |
| minecraft:yellow_wall_banner | составная | entity texture + цвет | стойка/полотно; базовый цвет без NBT-узоров |
| minecraft:yellow_wool | клиентский JSON | block texture | variants |
| minecraft:zombie_head | составная | entity/effect texture | моб-скин; player profile использует Steve |
| minecraft:zombie_wall_head | составная | entity/effect texture | моб-скин; player profile использует Steve |
