RIG_HEAD_PARTS = {
    "humanoid": {0}, "villager": {0}, "quadruped": {1}, "horse": {1},
    "camel": {1}, "creeper": {0}, "bird": {1}, "flying": {0}, "bat": {0},
    "bee": {0}, "fish": {0}, "squid": {0}, "arthropod": {0}, "cube": {0},
    "ghast": {0}, "golem": {0}, "turtle": {1}, "frog": {1}, "blaze": {0},
    "shulker": {0}, "dragon": {1}, "wither": {1, 2, 3},
}

DUMMY_RIGS = {
    "humanoid": (
        ((-.25, 1.45, -.25), (.25, 1.95, .25)),
        ((-.3, .65, -.18), (.3, 1.45, .18)),
        ((-.52, .65, -.14), (-.3, 1.4, .14)), ((.3, .65, -.14), (.52, 1.4, .14)),
        ((-.27, 0, -.14), (-.03, .65, .14)), ((.03, 0, -.14), (.27, .65, .14)),
    ),
    "villager": (
        ((-.28, 1.35, -.25), (.28, 1.95, .25)),
        ((-.08, 1.52, -.39), (.08, 1.72, -.25)),
        ((-.36, .35, -.22), (.36, 1.35, .22)),
        ((-.25, 0, -.16), (-.02, .35, .16)), ((.02, 0, -.16), (.25, .35, .16)),
    ),
    "quadruped": (
        ((-.42, .45, -.5), (.42, 1.05, .5)),
        ((-.34, .58, -.82), (.34, 1.12, -.5)),
        ((-.36, 0, -.42), (-.16, .5, -.2)), ((.16, 0, -.42), (.36, .5, -.2)),
        ((-.36, 0, .22), (-.16, .5, .44)), ((.16, 0, .22), (.36, .5, .44)),
    ),
    "horse": (
        ((-.42, .72, -.72), (.42, 1.42, .55)),
        ((-.3, 1.1, -.98), (.3, 1.75, -.58)),
        ((-.36, 0, -.58), (-.16, .78, -.36)), ((.16, 0, -.58), (.36, .78, -.36)),
        ((-.36, 0, .3), (-.16, .78, .52)), ((.16, 0, .3), (.36, .78, .52)),
    ),
    "camel": (
        ((-.5, .8, -.72), (.5, 1.55, .7)),
        ((-.28, 1.25, -.98), (.28, 2.35, -.58)),
        ((-.43, 0, -.58), (-.2, .9, -.34)), ((.2, 0, -.58), (.43, .9, -.34)),
        ((-.43, 0, .34), (-.2, .9, .58)), ((.2, 0, .34), (.43, .9, .58)),
    ),
    "creeper": (
        ((-.28, 1.25, -.28), (.28, 1.82, .28)), ((-.24, .45, -.2), (.24, 1.25, .2)),
        ((-.36, 0, -.35), (-.05, .48, -.05)), ((.05, 0, -.35), (.36, .48, -.05)),
        ((-.36, 0, .05), (-.05, .48, .35)), ((.05, 0, .05), (.36, .48, .35)),
    ),
    "bird": (
        ((-.22, .3, -.22), (.22, .82, .25)), ((-.17, .55, -.43), (.17, .88, -.2)),
        ((-.5, .46, -.08), (-.2, .72, .2)), ((.2, .46, -.08), (.5, .72, .2)),
        ((-.16, 0, -.04), (-.04, .34, .08)), ((.04, 0, -.04), (.16, .34, .08)),
    ),
    "flying": (
        ((-.22, .7, -.2), (.22, 1.18, .2)), ((-.28, .18, -.16), (.28, .7, .16)),
        ((-.7, .28, .04), (-.26, .9, .08)), ((.26, .28, .04), (.7, .9, .08)),
    ),
    "bat": (
        ((-.22, .35, -.18), (.22, .75, .18)),
        ((-.85, .25, -.04), (-.2, .75, .04)), ((.2, .25, -.04), (.85, .75, .04)),
    ),
    "bee": (
        ((-.35, .35, -.38), (.35, .9, .38)),
        ((-.68, .48, -.18), (-.32, .72, .2)), ((.32, .48, -.18), (.68, .72, .2)),
    ),
    "fish": (
        ((-.22, .25, -.55), (.22, .7, .55)), ((-.04, .3, .52), (.04, .65, .9)),
        ((-.45, .35, -.05), (.45, .42, .35)),
    ),
    "squid": (
        ((-.42, .7, -.42), (.42, 1.5, .42)),
        *((((x - .06, 0, z - .06), (x + .06, .75, z + .06))
           for x, z in ((-.3, -.3), (0, -.36), (.3, -.3), (-.36, 0),
                        (.36, 0), (-.3, .3), (0, .36), (.3, .3)))),
    ),
    "arthropod": (
        ((-.32, .2, -.58), (.32, .58, .15)), ((-.4, .18, .12), (.4, .62, .58)),
        *((((-.78, .1 + row * .1, z), (-.3, .2 + row * .1, z + .08))
           for row, z in enumerate((-.38, -.18, .08, .3)))),
        *((((.3, .1 + row * .1, z), (.78, .2 + row * .1, z + .08))
           for row, z in enumerate((-.38, -.18, .08, .3)))),
    ),
    "cube": (((-.45, 0, -.45), (.45, .9, .45)),),
    "ghast": (
        ((-.75, .8, -.75), (.75, 2.3, .75)),
        *((((x - .05, 0, z - .05), (x + .05, .85, z + .05))
           for x in (-.5, 0, .5) for z in (-.5, 0, .5))),
    ),
    "golem": (
        ((-.35, 1.45, -.32), (.35, 2.15, .32)), ((-.5, .65, -.28), (.5, 1.5, .28)),
        ((-.75, .45, -.2), (-.5, 1.45, .2)), ((.5, .45, -.2), (.75, 1.45, .2)),
        ((-.42, 0, -.22), (-.08, .7, .22)), ((.08, 0, -.22), (.42, .7, .22)),
    ),
    "turtle": (
        ((-.55, .18, -.65), (.55, .55, .65)), ((-.25, .2, -.92), (.25, .52, -.62)),
        ((-.85, .12, -.45), (-.5, .32, -.05)), ((.5, .12, -.45), (.85, .32, -.05)),
        ((-.8, .12, .1), (-.5, .32, .48)), ((.5, .12, .1), (.8, .32, .48)),
    ),
    "frog": (
        ((-.38, .18, -.35), (.38, .6, .35)), ((-.3, .35, -.58), (.3, .7, -.32)),
        ((-.55, 0, -.15), (-.22, .25, .35)), ((.22, 0, -.15), (.55, .25, .35)),
    ),
    "blaze": (
        ((-.28, 1.05, -.28), (.28, 1.62, .28)),
        *((((x - .05, .2 + row * .35, z - .05), (x + .05, .75 + row * .35, z + .05))
           for row, radius in enumerate((.55, .42, .55))
           for x, z in ((radius, 0), (0, radius), (-radius, 0), (0, -radius)))),
    ),
    "shulker": (
        ((-.48, 0, -.48), (.48, .42, .48)), ((-.48, .45, -.48), (.48, 1, .48)),
    ),
    "dragon": (
        ((-.55, .55, -.8), (.55, 1.35, .75)), ((-.42, .75, -1.35), (.42, 1.45, -.72)),
        ((-.08, .45, .65), (.08, 1.05, 1.8)),
        ((-2.2, .72, -.35), (-.5, .82, .9)), ((.5, .72, -.35), (2.2, .82, .9)),
        ((-.48, 0, -.35), (-.18, .65, .05)), ((.18, 0, -.35), (.48, .65, .05)),
    ),
    "wither": (
        ((-.75, 1.35, -.3), (.75, 1.7, .3)),
        ((-.25, 1.6, -.28), (.25, 2.1, .28)),
        ((-.95, 1.45, -.25), (-.55, 1.9, .25)), ((.55, 1.45, -.25), (.95, 1.9, .25)),
        ((-.12, .3, -.12), (.12, 1.4, .12)),
    ),
}

COMMON_DUMMY_RIGS = {
    "pig": (
        *DUMMY_RIGS["quadruped"],
        ((-.22, .68, -.94), (.22, .93, -.8)),
    ),
    "chicken": (
        *DUMMY_RIGS["bird"],
        ((-.12, .63, -.53), (.12, .78, -.42)),
        ((-.18, .42, .22), (.18, .7, .42)),
    ),
    "cow": (
        *DUMMY_RIGS["quadruped"],
        ((-.25, .65, -.94), (.25, .9, -.8)),
        ((-.38, .98, -.72), (-.27, 1.18, -.62)),
        ((.27, .98, -.72), (.38, 1.18, -.62)),
    ),
}


def _mob_specs():
    specs = {}

    def add(family, entries, scale=1.0):
        for kind, stems in entries.items():
            specs[kind] = (family, (stems,) if isinstance(stems, str) else stems, scale)

    add("flying", {
        "allay": "entity/allay/allay", "vex": "entity/illager/vex",
    })
    add("quadruped", {
        "armadillo": "entity/armadillo/armadillo", "goat": "entity/goat/goat",
        "mooshroom": ("entity/cow/mooshroom_red", "entity/cow/red_mooshroom"),
    })
    add("fish", {
        "axolotl": "entity/axolotl/axolotl_lucy", "cod": "entity/fish/cod",
        "dolphin": "entity/dolphin/dolphin", "elder_guardian": "entity/guardian/guardian_elder",
        "guardian": "entity/guardian/guardian", "nautilus": "entity/nautilus/nautilus",
        "pufferfish": "entity/fish/pufferfish", "salmon": "entity/fish/salmon",
        "tadpole": "entity/tadpole/tadpole", "tropical_fish": "entity/fish/tropical_a",
        "zombie_nautilus": "entity/nautilus/zombie_nautilus",
    })
    add("bat", {"bat": ("entity/bat/bat", "entity/bat")})
    add("bee", {"bee": "entity/bee/bee"})
    add("blaze", {"blaze": "entity/blaze/blaze", "breeze": "entity/breeze/breeze"})
    add("camel", {
        "camel": "entity/camel/camel", "camel_husk": "entity/camel/camel_husk",
    })
    add("quadruped", {
        "cat": "entity/cat/cat_tabby", "fox": "entity/fox/fox",
        "ocelot": "entity/cat/ocelot", "wolf": "entity/wolf/wolf",
    }, .72)
    add("arthropod", {
        "cave_spider": "entity/spider/cave_spider", "spider": "entity/spider/spider",
    })
    add("arthropod", {
        "endermite": "entity/endermite/endermite", "silverfish": "entity/silverfish/silverfish",
    }, .5)
    add("golem", {
        "copper_golem": "entity/copper_golem/copper_golem",
        "creaking": "entity/creaking/creaking",
        "iron_golem": "entity/iron_golem/iron_golem",
        "snow_golem": "entity/snow_golem/snow_golem", "warden": "entity/warden/warden",
    })
    add("creeper", {"creeper": "entity/creeper/creeper"})
    add("dragon", {"ender_dragon": "entity/enderdragon/dragon"}, 2.4)
    add("humanoid", {"enderman": "entity/enderman/enderman"}, 1.45)
    add("villager", {
        "evoker": "entity/illager/evoker", "illusioner": "entity/illager/illusioner",
        "pillager": "entity/illager/pillager", "vindicator": "entity/illager/vindicator",
        "villager": "entity/villager/villager",
        "wandering_trader": "entity/wandering_trader/wandering_trader",
        "witch": "entity/witch/witch", "zombie_villager": "entity/zombie_villager/zombie_villager",
    })
    add("ghast", {
        "ghast": "entity/ghast/ghast", "happy_ghast": "entity/ghast/happy_ghast",
    })
    add("humanoid", {"giant": "entity/zombie/zombie"}, 6.0)
    add("squid", {"glow_squid": "entity/squid/glow_squid", "squid": "entity/squid/squid"})
    add("quadruped", {
        "hoglin": "entity/hoglin/hoglin", "panda": "entity/panda/panda",
        "polar_bear": "entity/bear/polarbear", "ravager": "entity/illager/ravager",
        "sniffer": "entity/sniffer/sniffer", "zoglin": "entity/hoglin/zoglin",
    }, 1.35)
    add("horse", {
        "donkey": "entity/horse/donkey", "horse": "entity/horse/horse_brown",
        "mule": "entity/horse/mule", "skeleton_horse": "entity/horse/horse_skeleton",
        "zombie_horse": "entity/horse/horse_zombie",
    })
    add("horse", {
        "llama": "entity/llama/llama_brown", "trader_llama": "entity/llama/llama_creamy",
    }, 1.08)
    add("cube", {
        "magma_cube": "entity/slime/magmacube", "slime": "entity/slime/slime",
        "sulfur_cube": "entity/sulfur_cube/sulfur_cube_outer",
    })
    add("bird", {"parrot": "entity/parrot/parrot_red_blue"}, .75)
    add("flying", {"phantom": "entity/phantom/phantom"}, 1.5)
    add("humanoid", {
        "bogged": "entity/skeleton/bogged", "drowned": "entity/zombie/drowned",
        "husk": "entity/zombie/husk", "parched": "entity/skeleton/parched",
        "piglin": "entity/piglin/piglin", "piglin_brute": "entity/piglin/piglin_brute",
        "skeleton": "entity/skeleton/skeleton", "stray": "entity/skeleton/stray",
        "wither_skeleton": "entity/skeleton/wither_skeleton",
        "zombified_piglin": "entity/piglin/zombified_piglin",
    })
    add("quadruped", {"rabbit": "entity/rabbit/rabbit_brown"}, .55)
    add("shulker", {"shulker": "entity/shulker/shulker"})
    add("bird", {"strider": "entity/strider/strider"}, 1.15)
    add("frog", {"frog": ("entity/frog/frog_temperate", "entity/frog/temperate_frog")})
    add("turtle", {"turtle": "entity/turtle/turtle"})
    add("wither", {"wither": "entity/wither/wither"}, 1.5)
    return specs


MOB_SPECS = _mob_specs()

_COMMON_MOBS = {
    "chicken": ("bird", ("entity/chicken/chicken_temperate", "entity/chicken"), 1.0),
    "cow": ("quadruped", ("entity/cow/cow_temperate", "entity/cow/cow"), 1.0),
    "pig": ("quadruped", ("entity/pig/pig_temperate", "entity/pig/pig"), 1.0),
    "sheep": ("quadruped", ("entity/sheep/sheep",), 1.0),
    "zombie": ("humanoid", ("entity/zombie/zombie",), 1.0),
}
