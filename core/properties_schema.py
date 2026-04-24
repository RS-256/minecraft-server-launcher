# Schema definitions for Minecraft server.properties

KNOWN_PROPERTIES: dict[str, dict] = {
    "server-port":          {"type": "int",    "default": 25565, "min": 1, "max": 65535},
    "query.port":           {"type": "int",    "default": 25565, "min": 1, "max": 65535},
    "max-players":          {"type": "int",    "default": 20,    "min": 1, "max": 1000},
    "spawn-protection":     {"type": "int",    "default": 16,    "min": 0, "max": 256},
    "view-distance":        {"type": "int",    "default": 10,    "min": 3, "max": 32},
    "simulation-distance":  {"type": "int",    "default": 10,    "min": 3, "max": 32},
    "max-world-size":       {"type": "int",    "default": 29999984, "min": 1, "max": 29999984},
    "op-permission-level":  {"type": "int",    "default": 4,     "min": 1, "max": 4},
    "max-build-height":     {"type": "int",    "default": 256,   "min": 0, "max": 256},
    "rate-limit":           {"type": "int",    "default": 0,     "min": 0, "max": 9999},
    "entity-broadcast-range-percentage": {
        "type": "int", "default": 100, "min": 10, "max": 1000
    },
    "rcon.port":            {"type": "int",    "default": 25575, "min": 1, "max": 65535},

    "online-mode":              {"type": "bool", "default": True},
    "white-list":               {"type": "bool", "default": False},
    "pvp":                      {"type": "bool", "default": True},
    "hardcore":                 {"type": "bool", "default": False},
    "allow-flight":             {"type": "bool", "default": False},
    "allow-nether":             {"type": "bool", "default": True},
    "spawn-monsters":           {"type": "bool", "default": True},
    "spawn-animals":            {"type": "bool", "default": True},
    "spawn-npcs":               {"type": "bool", "default": True},
    "generate-structures":      {"type": "bool", "default": True},
    "enable-command-block":     {"type": "bool", "default": False},
    "enable-query":             {"type": "bool", "default": False},
    "enable-rcon":              {"type": "bool", "default": False},
    "enable-jmx-monitoring":    {"type": "bool", "default": False},
    "sync-chunk-writes":        {"type": "bool", "default": True},
    "force-gamemode":           {"type": "bool", "default": False},
    "broadcast-console-to-ops": {"type": "bool", "default": True},
    "broadcast-rcon-to-ops":    {"type": "bool", "default": True},
    "require-resource-pack":    {"type": "bool", "default": False},
    "hide-online-players":      {"type": "bool", "default": False},
    "previews-chat":            {"type": "bool", "default": False},
    "enforce-secure-profile":   {"type": "bool", "default": True},
    "enforce-whitelist":        {"type": "bool", "default": False},
    "log-ips":                  {"type": "bool", "default": True},

    "gamemode": {
        "type": "combo",
        "default": "survival",
        "choices": ["survival", "creative", "adventure", "spectator"]
    },
    "difficulty": {
        "type": "combo",
        "default": "easy",
        "choices": ["peaceful", "easy", "normal", "hard"]
    },
    "level-type": {
        "type": "combo",
        "default": "minecraft:normal",
        "choices": [
            "minecraft:normal", "minecraft:flat",
            "minecraft:large_biomes", "minecraft:amplified",
            "minecraft:single_biome_surface"
        ]
    },

    "level-name":            {"type": "str", "default": "world"},
    "level-seed":            {"type": "str", "default": ""},
    "motd":                  {"type": "str", "default": "A Minecraft Server"},
    "server-ip":             {"type": "str", "default": ""},
    "resource-pack":         {"type": "str", "default": ""},
    "resource-pack-sha1":    {"type": "str", "default": ""},
    "resource-pack-prompt":  {"type": "str", "default": ""},
    "rcon.password":         {"type": "str", "default": ""},
    "text-filtering-config": {"type": "str", "default": ""},
}

# Properties shown first in the UI
PRIORITY_KEYS: list[str] = [
    "server-port",
    "max-players",
    "gamemode",
    "difficulty",
    "level-name",
    "level-seed",
    "online-mode",
    "white-list",
    "pvp",
    "hardcore",
    "motd",
    "view-distance",
    "simulation-distance",
    "spawn-protection",
    "enable-command-block",
    "allow-flight",
]
