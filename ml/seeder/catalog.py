# =========================================================
# DATA CATALOG — Enriched for 4000+ products
# =========================================================
# Structure: CATALOG[category][subcategory] = {brands, name_parts, features}
# Each subcategory has 10+ brands, 20+ name_parts, 10+ features
# for maximum combinatorial diversity and minimal repetition.
# =========================================================

CATALOG = {

    # -------------------------------------------------------
    # 1. ELECTRONICS
    # -------------------------------------------------------
    "electronics": {
        "smartphones": {
            "brands": [
                "Apple", "Samsung", "Xiaomi", "OnePlus", "Huawei", "Google",
                "Oppo", "Sony", "Nokia", "Motorola", "Realme", "Vivo",
                "Asus", "ZTE", "Tecno", "Infinix", "Honor", "Nothing",
                "BlackBerry", "Fairphone",
            ],
            "name_parts": [
                "Pro", "Max", "Lite", "Ultra", "Edge", "Plus", "Neo", "Prime",
                "Fold", "Flip", "Slim", "Note", "Air", "Spark", "Vision",
                "Flash", "Pulse", "Apex", "Zenith", "Nova", "Series", "X",
                "GT", "SE", "Mini", "Active", "Turbo", "Fusion", "Elite",
                "Legend",
            ],
            "features": [
                "battery life", "camera quality", "screen resolution",
                "performance", "charging speed", "build quality", "AI features",
                "5G connectivity", "display refresh rate", "processor speed",
                "water resistance", "storage capacity", "fingerprint sensor",
                "face recognition", "audio quality",
            ],
        },
        "laptops": {
            "brands": [
                "Dell", "HP", "Lenovo", "Asus", "Acer", "MSI", "Apple",
                "Razer", "Microsoft", "Samsung", "Huawei", "LG", "Toshiba",
                "Vaio", "Gigabyte", "Framework", "System76", "Alienware",
                "Chuwi", "Mechrevo",
            ],
            "name_parts": [
                "Book", "Air", "Pro", "Flex", "Think", "Studio", "Slim",
                "Core", "Zen", "Spectre", "Pavilion", "IdeaPad", "VivoBook",
                "ZenBook", "Swift", "Predator", "Nitro", "Inspiron", "Envy",
                "EliteBook", "XPS", "Blade", "Surface", "MateBook", "Gram",
                "Portege", "Chromebook", "Gaming", "Ultrabook",
            ],
            "features": [
                "keyboard feel", "processor performance", "OLED display",
                "battery life", "cooling system", "build quality", "weight",
                "RAM speed", "SSD read speed", "screen color accuracy",
                "GPU performance", "USB-C charging", "touchpad responsiveness",
                "speaker quality", "webcam quality",
            ],
        },
        "tablets": {
            "brands": [
                "Apple", "Samsung", "Lenovo", "Huawei", "Xiaomi", "Amazon",
                "Microsoft", "Asus", "Chuwi", "TCL", "Realme", "Nokia",
                "Onyx Boox", "reMarkable", "Google",
            ],
            "name_parts": [
                "Tab", "Pad", "Air", "Mini", "Pro", "Go", "Fire", "Lite",
                "Plus", "Max", "S", "Ultra", "Note", "Surface", "MatePad",
                "MiPad", "Galaxy", "iPad", "Flex", "Duo",
            ],
            "features": [
                "screen resolution", "battery endurance", "portability",
                "performance", "stylus support", "keyboard compatibility",
                "display brightness", "multitasking", "reading mode",
                "audio output", "build quality", "charging speed",
            ],
        },
        "headphones": {
            "brands": [
                "Sony", "JBL", "Bose", "Apple", "Samsung", "Anker",
                "Logitech", "Sennheiser", "Audio-Technica", "Jabra",
                "Beats", "Skullcandy", "Plantronics", "Bang & Olufsen",
                "Beyerdynamic", "AKG", "Shure", "Edifier", "1More", "Nothing",
            ],
            "name_parts": [
                "Sound", "Beat", "Air", "Pods", "Studio", "Wave", "Tune",
                "Quiet", "Momentum", "Elite", "Evolve", "Fit", "Live",
                "Zone", "Sense", "Drift", "Crush", "Bass", "Hybrid",
                "Odyssey", "Flex", "Tone", "Arc", "Space", "Pulse",
            ],
            "features": [
                "sound quality", "comfort", "battery life",
                "noise cancellation", "design", "microphone clarity",
                "bass depth", "treble accuracy", "soundstage width",
                "call quality", "wireless range", "ear cushion material",
                "touch controls", "codec support", "latency",
            ],
        },
        "cameras": {
            "brands": [
                "Canon", "Nikon", "Sony", "Fujifilm", "Panasonic",
                "GoPro", "DJI", "Olympus", "Leica", "Hasselblad",
                "Kodak", "Ricoh", "Sigma", "Pentax",
            ],
            "name_parts": [
                "Shot", "Zoom", "Vision", "Capture", "Snap", "Focus",
                "Alpha", "EOS", "Lumix", "Rebel", "Z-Series", "Cyber",
                "Hero", "Mini", "Action", "Mirrorless", "Medium",
                "Compact", "SLR", "DSLR",
            ],
            "features": [
                "image sharpness", "optical zoom range", "autofocus speed",
                "battery life", "video stabilization", "low-light performance",
                "burst shooting speed", "RAW support", "weather sealing",
                "viewfinder resolution", "flip screen usability",
                "connectivity options", "menu intuitiveness",
            ],
        },
        "smartwatches": {
            "brands": [
                "Apple", "Samsung", "Garmin", "Fitbit", "Huawei",
                "Xiaomi", "Amazfit", "Fossil", "Withings", "Polar",
                "Suunto", "TicWatch", "OnePlus", "Google", "Mobvoi",
            ],
            "name_parts": [
                "Watch", "Band", "Fit", "Health", "Active", "Series",
                "Pro", "Ultra", "GT", "GTS", "GTR", "Verge", "Sense",
                "Vantage", "Fenix", "Forerunner", "Charge", "Luxe",
                "Halo", "Pixel",
            ],
            "features": [
                "health tracking accuracy", "battery life", "GPS precision",
                "heart rate monitoring", "sleep tracking", "water resistance",
                "display clarity", "notification management", "fitness modes",
                "VO2 max measurement", "ECG capability", "custom watch faces",
            ],
        },
        "televisions": {
            "brands": [
                "Samsung", "LG", "Sony", "Philips", "TCL", "Hisense",
                "Xiaomi", "Panasonic", "Sharp", "Toshiba", "Vizio",
                "Haier", "Skyworth", "Changhong",
            ],
            "name_parts": [
                "QLED", "OLED", "Neo", "Crystal", "Smart", "4K", "8K",
                "Pro", "Ultra", "Vision", "Frame", "Serif", "Bravia",
                "Nanocell", "MiniLED", "Quantum", "Lifestyle", "Art",
                "QNED", "Master",
            ],
            "features": [
                "picture quality", "contrast ratio", "HDR performance",
                "black levels", "color gamut", "refresh rate", "input lag",
                "upscaling quality", "smart OS responsiveness", "remote usability",
                "sound output", "HDMI 2.1 support", "viewing angles",
            ],
        },
    },

    # -------------------------------------------------------
    # 2. BEAUTY & PERSONAL CARE
    # -------------------------------------------------------
    "beauty": {
        "skincare": {
            "brands": [
                "CeraVe", "Vichy", "Nivea", "La Roche-Posay", "Garnier",
                "Bioderma", "Clinique", "Neutrogena", "The Ordinary",
                "Paula's Choice", "Drunk Elephant", "The Inkey List",
                "Kiehl's", "Origins", "First Aid Beauty", "Murad",
                "Sunday Riley", "Tatcha", "COSRX", "Skin1004",
            ],
            "name_parts": [
                "Glow", "Hydra", "Pure", "Fresh", "Calm", "Care", "Vital",
                "Balance", "Radiance", "Barrier", "Repair", "Renew",
                "Serum", "Essence", "Toner", "Mist", "Shield", "Boost",
                "Revive", "Detox", "Pore", "Bright", "Firm", "Soothe",
            ],
            "features": [
                "texture", "hydration level", "anti-aging effect",
                "value for price", "fragrance intensity", "skin absorption",
                "pore minimizing", "brightening effect", "sensitive skin safety",
                "SPF protection", "active ingredient potency", "packaging quality",
                "shelf life", "consistency",
            ],
        },
        "makeup": {
            "brands": [
                "Maybelline", "L'Oréal", "Sephora Collection", "NYX",
                "MAC", "Essence", "Fenty Beauty", "Charlotte Tilbury",
                "Too Faced", "Urban Decay", "NARS", "Huda Beauty",
                "e.l.f.", "Rare Beauty", "ColourPop", "Milani",
                "Wet n Wild", "Barry M", "Revolution", "Morphe",
            ],
            "name_parts": [
                "Color", "Shine", "Soft", "Velvet", "Matte", "Glow",
                "Lush", "Tint", "Flush", "Satin", "Dewy", "Flawless",
                "HD", "Longwear", "Ultra", "Sheer", "Metallic", "Buildable",
                "Sculpt", "Contour", "Blush", "Bronze", "Highlight",
                "Flushed",
            ],
            "features": [
                "coverage level", "texture", "color range", "wear duration",
                "pigmentation intensity", "crease resistance", "transfer-proof quality",
                "blendability", "finish type", "shade inclusivity",
                "applicator quality", "packaging elegance", "formula composition",
            ],
        },
        "haircare": {
            "brands": [
                "Dove", "Pantene", "L'Oréal", "Garnier", "Élsève",
                "Head & Shoulders", "Kérastase", "Olaplex", "Redken",
                "Wella", "Paul Mitchell", "John Frieda", "Moroccanoil",
                "OGX", "Batiste", "Aussie", "Tresemmé", "Matrix",
                "Aveda", "R+Co",
            ],
            "name_parts": [
                "Repair", "Smooth", "Silk", "Care", "Nutri", "Shine",
                "Volumize", "Hydrate", "Bond", "Curl", "Frizz", "Scalp",
                "Color", "Cleanse", "Detangle", "Strengthen", "Restore",
                "Therapy", "Gloss", "Perfection",
            ],
            "features": [
                "fragrance quality", "shine effect", "texture improvement",
                "effectiveness on damage", "sulfate-free formula",
                "scalp health", "lather quality", "moisture retention",
                "color protection", "heat protection", "frizz control",
                "detangling ease", "ingredient safety",
            ],
        },
        "fragrance": {
            "brands": [
                "Dior", "Chanel", "Yves Saint Laurent", "Armani",
                "Zara", "Versace", "Tom Ford", "Givenchy", "Guerlain",
                "Hermès", "Prada", "Montblanc", "Burberry", "Dolce &Gabbana",
                "Jean Paul Gaultier", "Calvin Klein", "Hugo Boss",
                "Viktor & Rolf", "Jo Malone", "Byredo",
            ],
            "name_parts": [
                "Bloom", "Secret", "Night", "Rose", "Fresh", "Aura",
                "Noir", "Oud", "Intense", "Wood", "Aqua", "Bleu",
                "Gold", "Velvet", "Amber", "Musk", "Ocean", "Citrus",
                "Elixir", "Pure", "Flora", "Infusion", "Sauvage", "Libre",
            ],
            "features": [
                "top notes", "longevity", "bottle design aesthetics",
                "sillage", "uniqueness", "season suitability", "base notes",
                "projection", "price per ml", "occasion versatility",
                "complexity", "gender blending",
            ],
        },
        "personal_hygiene": {
            "brands": [
                "Dove", "Nivea", "Gillette", "Oral-B", "Colgate",
                "Listerine", "Vaseline", "Dettol", "Savlon", "Rexona",
                "Axe", "Old Spice", "Palmolive", "Crest", "Sensodyne",
            ],
            "name_parts": [
                "Fresh", "Clean", "Pure", "Active", "Protect", "Shield",
                "Cool", "Natural", "Sensitive", "Whitening", "Defend",
                "Gentle", "Comfort", "Refresh", "Balance",
            ],
            "features": [
                "fragrance", "skin compatibility", "lasting protection",
                "effectiveness", "packaging convenience", "formula gentleness",
                "moisturizing effect", "antibacterial power", "value pack size",
            ],
        },
    },

    # -------------------------------------------------------
    # 3. HOME APPLIANCES
    # -------------------------------------------------------
    "home_appliances": {
        "kitchen_appliances": {
            "brands": [
                "Philips", "Tefal", "Moulinex", "Bosch", "LG", "Samsung",
                "Panasonic", "KitchenAid", "Braun", "Kenwood", "Ninja",
                "Instant Pot", "Cuisinart", "Delonghi", "Electrolux",
                "Whirlpool", "Breville", "Midea", "Smeg", "Hamilton Beach",
            ],
            "name_parts": [
                "Cook", "Chef", "Mix", "Smart", "Home", "Easy", "Blend",
                "Grill", "Steam", "Express", "Master", "Vital", "Speedy",
                "Auto", "Pro", "Quick", "Turbo", "Multi", "Classic",
                "Select",
            ],
            "features": [
                "power output", "durability", "design aesthetics",
                "ease of cleaning", "ease of use", "safety mechanisms",
                "noise level", "cooking evenness", "capacity", "energy efficiency",
                "timer functionality", "material quality", "versatility",
            ],
        },
        "cleaning_devices": {
            "brands": [
                "Dyson", "Philips", "Samsung", "Bosch", "Kärcher",
                "Shark", "iRobot", "Miele", "Rowenta", "Hoover",
                "Bissell", "Tineco", "Dreame", "Roborock", "Ecovacs",
            ],
            "name_parts": [
                "Clean", "Turbo", "Power", "Fresh", "Sweep", "Vac",
                "Bot", "Slim", "Cyclone", "Deep", "Smart", "Auto",
                "Laser", "Boost", "Cordless",
            ],
            "features": [
                "suction power", "filter quality", "battery runtime",
                "maneuverability", "smart navigation", "mopping function",
                "dustbin capacity", "noise level", "obstacle detection",
                "mapping accuracy", "self-emptying base", "cord management",
            ],
        },
        "air_conditioning": {
            "brands": [
                "LG", "Samsung", "Gree", "Midea", "Hisense", "Daikin",
                "Mitsubishi", "Hitachi", "Haier", "Fujitsu", "Toshiba",
                "Carrier", "York", "Panasonic",
            ],
            "name_parts": [
                "Cool", "Breeze", "Air", "Fresh", "Comfort", "Inverter",
                "Eco", "Dual", "Stream", "Arctic", "Flow", "Whisper",
                "Hyper", "Pure", "Wind",
            ],
            "features": [
                "cooling speed", "heating mode efficiency", "noise level",
                "energy efficiency rating", "smart controls", "air purification",
                "dehumidification", "filter maintenance", "installation ease",
                "remote control quality", "compressor durability",
            ],
        },
        "washing_machines": {
            "brands": [
                "Samsung", "LG", "Bosch", "Whirlpool", "Beko",
                "Electrolux", "Haier", "Siemens", "Hotpoint", "Ariston",
                "Zanussi", "AEG", "Indesit", "Panasonic", "Midea",
            ],
            "name_parts": [
                "Wash", "Clean", "Expert", "ActiveCare", "EcoSmart",
                "HygienePlus", "QuickWash", "VaporCare", "AddWash",
                "TurboWash", "SteamWash", "DirectDrive", "Inverter",
                "EcoSilence", "Crystal",
            ],
            "features": [
                "washing performance", "spin speed", "energy class",
                "noise level", "drum capacity", "cycle duration",
                "stain removal power", "water consumption", "smart connectivity",
                "vibration control", "self-cleaning drum",
            ],
        },
        "refrigerators": {
            "brands": [
                "Samsung", "LG", "Bosch", "Whirlpool", "Siemens",
                "Liebherr", "Haier", "Electrolux", "Beko", "Hisense",
                "Miele", "Sub-Zero", "Fisher & Paykel", "Gorenje",
            ],
            "name_parts": [
                "FreshPlus", "NoFrost", "MultiFlow", "CoolPlus", "IceMaker",
                "FamilyHub", "EcoFlex", "TwinCooling", "BioFresh", "HydroFresh",
                "PureFresh", "InstaView", "Door-in-Door", "SmartSense",
                "VarioSpace",
            ],
            "features": [
                "temperature stability", "energy efficiency", "freezer capacity",
                "freshness preservation", "noise level", "smart features",
                "ice maker quality", "door organization", "compressor reliability",
                "lighting quality", "humidity control",
            ],
        },
    },

    # -------------------------------------------------------
    # 4. COMPUTERS & ACCESSORIES
    # -------------------------------------------------------
    "computers": {
        "desktop_pc": {
            "brands": [
                "Dell", "HP", "Lenovo", "Asus", "Acer", "MSI",
                "Corsair", "Origin PC", "CyberPowerPC", "iBUYPOWER",
                "Apple", "System76", "Alienware", "NZXT",
            ],
            "name_parts": [
                "Tower", "Core", "Vision", "Pro", "Power", "Station",
                "Elite", "Compact", "Mini", "Gaming", "Creator",
                "Workstation", "Studio", "One", "Ultra",
            ],
            "features": [
                "gaming performance", "cooling efficiency", "case design",
                "upgrade potential", "value for price", "RAM expandability",
                "storage options", "GPU slot support", "power supply quality",
                "RGB lighting", "noise level", "build quality",
            ],
        },
        "computer_accessories": {
            "brands": [
                "Logitech", "Razer", "Corsair", "HP", "Dell", "Asus",
                "Keychron", "SteelSeries", "HyperX", "Elgato",
                "Anker", "Belkin", "CalDigit", "Plugable", "Kensington",
            ],
            "name_parts": [
                "Mouse", "Key", "Hub", "Link", "Pad", "Dock", "Switch",
                "Pro", "Elite", "Slim", "Mini", "Pebble", "MX", "G",
                "K", "Stream", "Wave", "Orbweaver", "Nomad",
            ],
            "features": [
                "ergonomics", "comfort during long sessions", "build quality",
                "connectivity options", "polling rate", "click feel",
                "RGB customization", "wireless reliability", "price",
                "macro programmability", "compatibility", "cable quality",
            ],
        },
        "storage_devices": {
            "brands": [
                "Samsung", "Kingston", "SanDisk", "WD", "Seagate",
                "Crucial", "Corsair", "Lexar", "PNY", "ADATA",
                "Silicon Power", "Toshiba", "Transcend", "OWC",
            ],
            "name_parts": [
                "Drive", "Store", "Flash", "Secure", "Speed", "Vault",
                "NVMe", "Evo", "Pro", "Ultra", "Extreme", "Barracuda",
                "FireCuda", "IronWolf", "WD Blue",
            ],
            "features": [
                "sequential read speed", "sequential write speed",
                "random IOPS", "storage capacity", "heat generation",
                "durability under shock", "form factor compatibility",
                "warranty length", "value per GB", "power consumption",
            ],
        },
        "monitors": {
            "brands": [
                "Samsung", "LG", "Dell", "Asus", "Acer", "BenQ",
                "ViewSonic", "AOC", "Gigabyte", "MSI", "Philips",
                "HP", "Alienware", "Viotek",
            ],
            "name_parts": [
                "UltraWide", "Curved", "4K", "OLED", "IPS", "VA",
                "ProArt", "Gaming", "Odyssey", "UltraSharp", "Predator",
                "ViewFinity", "Nitro", "EW", "EX",
            ],
            "features": [
                "panel color accuracy", "refresh rate", "response time",
                "resolution", "HDR brightness", "ergonomic adjustability",
                "eye care technology", "port selection", "ultrawide productivity",
                "pixel density", "contrast ratio",
            ],
        },
    },

    # -------------------------------------------------------
    # 5. GAMING
    # -------------------------------------------------------
    "gaming": {
        "gaming_consoles": {
            "brands": [
                "Sony", "Microsoft", "Nintendo", "Asus", "Valve",
                "Atari", "Evercade", "Analogue",
            ],
            "name_parts": [
                "Play", "Box", "Next", "Arena", "Game", "Zone",
                "Deck", "Pocket", "Link", "Neo", "Turbo", "Edge",
                "Station", "Switch", "Series",
            ],
            "features": [
                "graphics performance", "exclusive game library",
                "controller ergonomics", "load time speed",
                "backward compatibility", "online service quality",
                "storage expandability", "portable mode quality",
                "media center functionality",
            ],
        },
        "gaming_accessories": {
            "brands": [
                "Razer", "Logitech", "Corsair", "SteelSeries", "HyperX",
                "Turtle Beach", "Astro", "Scuf", "Thrustmaster", "Hori",
                "8BitDo", "PowerA", "Victrix",
            ],
            "name_parts": [
                "Gear", "Elite", "Pro", "Strike", "Boost", "Pulse",
                "Wired", "Nari", "Arctis", "Kraken", "Earforce",
                "A50", "Wildcat", "Talon", "CloudX",
            ],
            "features": [
                "comfort during long sessions", "audio response time",
                "design", "durability under heavy use", "value for price",
                "trigger sensitivity", "haptic feedback", "wireless latency",
                "microphone quality for comms", "lighting effects",
            ],
        },
        "gaming_chairs": {
            "brands": [
                "DXRacer", "Secretlab", "Razer", "Corsair", "Asus",
                "Noblechairs", "AndaSeat", "Herman Miller", "Vertagear",
                "Cluvens", "AKRacing", "GTRACING",
            ],
            "name_parts": [
                "Seat", "Comfort", "Throne", "Elite", "Pro", "Titan",
                "Omega", "Formula", "Hero", "King", "Ace", "Magnus",
                "Prime", "Cloud", "Embody",
            ],
            "features": [
                "lumbar support quality", "armrest adjustability",
                "seat foam density", "recline range", "tilt mechanism",
                "material durability", "breathability", "height adjustment",
                "assembly ease", "stitching quality",
            ],
        },
        "gaming_headsets": {
            "brands": [
                "SteelSeries", "HyperX", "Razer", "Astro", "Logitech",
                "Turtle Beach", "Corsair", "JBL", "Sony", "Epos",
            ],
            "name_parts": [
                "Arctis", "Cloud", "Kraken", "A50", "G733", "Earforce",
                "Virtuoso", "Quantum", "Void", "Rig",
            ],
            "features": [
                "surround sound accuracy", "microphone clarity",
                "comfort for marathon sessions", "wireless range",
                "battery life", "platform compatibility", "noise isolation",
                "chat-to-game audio balance", "RGB customization",
            ],
        },
    },

    # -------------------------------------------------------
    # 6. SPORTS & OUTDOOR
    # -------------------------------------------------------
    "sports": {
        "fitness_equipment": {
            "brands": [
                "Bowflex", "NordicTrack", "Peloton", "Life Fitness",
                "Technogym", "Reebok", "Adidas", "JLL", "Marcy",
                "Body-Solid", "PowerBlock", "Rogue", "Sunny Health",
                "Concept2", "WaterRower",
            ],
            "name_parts": [
                "Power", "Pro", "Elite", "Max", "Active", "Fit",
                "Strong", "Endure", "Cardio", "Flex", "Core", "Boost",
                "Cycle", "Trainer", "Glide",
            ],
            "features": [
                "resistance range", "cushioning quality", "build sturdiness",
                "monitor accuracy", "folding mechanism", "noise level",
                "weight capacity", "setup ease", "workout variety",
                "connectivity to apps", "flywheel smoothness",
            ],
        },
        "running_shoes": {
            "brands": [
                "Nike", "Adidas", "New Balance", "Brooks", "HOKA",
                "Asics", "Saucony", "Salomon", "Mizuno", "On Running",
                "Puma", "Reebok", "Altra", "Vans", "Merrell",
            ],
            "name_parts": [
                "Air", "Boost", "Cloud", "Gel", "Cushion", "Speed",
                "Race", "Trail", "Ultra", "Endure", "Stride", "Wave",
                "Zoom", "Kinvara", "Fresh",
            ],
            "features": [
                "cushioning responsiveness", "stability", "breathability",
                "durability of outsole", "heel-to-toe drop", "weight",
                "toe box width", "arch support", "aesthetics", "water resistance",
                "return energy", "grip on wet surfaces",
            ],
        },
        "cycling": {
            "brands": [
                "Trek", "Giant", "Specialized", "Cannondale", "Scott",
                "Merida", "Cube", "BMC", "Orbea", "Canyon",
                "Shimano", "SRAM", "Bianchi", "Pinarello",
            ],
            "name_parts": [
                "Road", "Mountain", "Gravel", "Hybrid", "Electric",
                "Carbon", "Alloy", "Race", "Trail", "City",
                "Commute", "X", "Ultra", "Swift", "Evo",
            ],
            "features": [
                "gear shifting precision", "frame stiffness",
                "brake responsiveness", "wheel rolling resistance",
                "handlebar comfort", "saddle quality", "weight",
                "aerodynamics", "tubeless compatibility",
            ],
        },
        "sportswear": {
            "brands": [
                "Nike", "Adidas", "Under Armour", "Puma", "Reebok",
                "New Balance", "Lululemon", "Gymshark", "Fabletics",
                "Columbia", "Patagonia", "The North Face", "Arc'teryx",
                "Salomon", "Odlo",
            ],
            "name_parts": [
                "Dri-Fit", "Pro", "Performance", "Flex", "Move",
                "Active", "Speed", "Power", "Endure", "Core",
                "Aerochill", "Warpknit", "Climalite", "Seamless", "Mesh",
            ],
            "features": [
                "moisture wicking", "stretch flexibility", "breathability",
                "seam placement", "fabric feel", "durability after washing",
                "compression level", "odor resistance", "UV protection",
                "pocket design", "waistband comfort",
            ],
        },
    },

    # -------------------------------------------------------
    # 7. FASHION
    # -------------------------------------------------------
    "fashion": {
        "mens_clothing": {
            "brands": [
                "Zara", "H&M", "Uniqlo", "Calvin Klein", "Tommy Hilfiger",
                "Ralph Lauren", "Levi's", "Hugo Boss", "Lacoste",
                "Ben Sherman", "Jack & Jones", "Selected Homme",
                "Massimo Dutti", "Banana Republic", "G-Star",
            ],
            "name_parts": [
                "Slim", "Tapered", "Relaxed", "Regular", "Oxford",
                "Chino", "Merino", "Bomber", "Performance", "Oxford",
                "Flannel", "Cashmere", "Linen", "Stretch", "Technical",
            ],
            "features": [
                "fabric quality", "fit accuracy", "stitching durability",
                "color fastness", "comfort", "wash-and-wear performance",
                "versatility for occasions", "button quality",
                "pocket functionality",
            ],
        },
        "womens_clothing": {
            "brands": [
                "Zara", "H&M", "Uniqlo", "Mango", "ASOS",
                "Anthropologie", "Free People", "Reformation",
                "& Other Stories", "COS", "Weekday", "Monki",
                "Eileen Fisher", "Everlane", "Treasure & Bond",
            ],
            "name_parts": [
                "Wrap", "Midi", "Maxi", "Mini", "Flared", "Fitted",
                "Relaxed", "Cropped", "Drape", "Ruffle", "Pleated",
                "Asymmetric", "Knit", "Woven", "Printed",
            ],
            "features": [
                "fabric drape", "sizing accuracy", "color vibrancy",
                "construction quality", "comfort", "occasionality",
                "pocket depth", "lining quality", "zipper smoothness",
                "shrinkage after washing",
            ],
        },
        "footwear": {
            "brands": [
                "Nike", "Adidas", "Converse", "Vans", "Dr. Martens",
                "Birkenstock", "Clarks", "Timberland", "Ecco",
                "Steve Madden", "Aldo", "Tommy Hilfiger", "Fila",
                "UGG", "Crocs",
            ],
            "name_parts": [
                "Classic", "Low", "High", "Platform", "Chunky",
                "Slip-On", "Lace-Up", "Chelsea", "Derby", "Oxford",
                "Loafer", "Boot", "Mule", "Sandal", "Sneaker",
            ],
            "features": [
                "sole grip", "arch support quality", "break-in period",
                "material durability", "true to size", "breathability",
                "waterproofing", "cushioning", "ankle support",
                "aesthetic design", "versatility",
            ],
        },
        "bags_accessories": {
            "brands": [
                "Samsonite", "Herschel", "JanSport", "Fjällräven",
                "Osprey", "Eastpak", "Fossil", "Michael Kors",
                "Coach", "Kate Spade", "Longchamp", "Tumi",
                "Briggs & Riley", "Peak Design",
            ],
            "name_parts": [
                "Slim", "Tech", "Heritage", "Travel", "Compact",
                "Everyday", "Adventure", "Durable", "Lite", "Classic",
                "Pro", "Mini", "Rolltop", "Commuter", "Weekender",
            ],
            "features": [
                "storage capacity", "compartment organization",
                "strap comfort", "zipper quality", "water resistance",
                "material durability", "laptop sleeve fit",
                "aesthetics", "weight", "expandability",
            ],
        },
    },

    # -------------------------------------------------------
    # 8. BOOKS & STATIONERY
    # -------------------------------------------------------
    "books_stationery": {
        "fiction_books": {
            "brands": [
                "Penguin Random House", "HarperCollins", "Simon & Schuster",
                "Hachette", "Macmillan", "Tor Books", "Orbit", "Del Rey",
                "Bloomsbury", "Picador", "Vintage Books", "Anchor",
            ],
            "name_parts": [
                "Chronicles", "Legacy", "Shadow", "Dawn", "Echo",
                "Realm", "Forgotten", "Lost", "Hidden", "Shattered",
                "Rising", "Fallen", "Eternal", "Infinite", "Broken",
            ],
            "features": [
                "plot pacing", "character development", "world-building depth",
                "prose style", "dialogue quality", "ending satisfaction",
                "emotional impact", "originality", "page count value",
                "re-read worthiness",
            ],
        },
        "non_fiction_books": {
            "brands": [
                "Penguin Books", "Portfolio", "Crown Publishing",
                "Harvard Business Review Press", "MIT Press", "Oxford University Press",
                "Chronicle Books", "Rodale Books", "Wiley", "O'Reilly Media",
            ],
            "name_parts": [
                "Principles", "Mindset", "Strategy", "Habits", "Formula",
                "Blueprint", "Framework", "Code", "Design", "Method",
                "Science", "Art", "Philosophy", "History", "Guide",
            ],
            "features": [
                "factual accuracy", "research depth", "readability",
                "applicability of ideas", "structure clarity",
                "index and reference quality", "academic rigor",
                "practical examples", "citation quality",
            ],
        },
        "stationery": {
            "brands": [
                "Moleskine", "Leuchtturm1917", "Rhodia", "Staedtler",
                "Pilot", "Uni-ball", "Zebra", "Clairefontaine",
                "Muji", "Midori", "Field Notes", "Pentel", "Tombow",
            ],
            "name_parts": [
                "Classic", "Slim", "Squared", "Dotted", "Lined",
                "Hardcover", "Soft", "Traveler", "Pocket", "A5",
                "Pro", "Daily", "Weekly", "Planner", "Journal",
            ],
            "features": [
                "paper quality (bleed-through)", "cover durability",
                "binding type", "page count", "ruling quality",
                "portability", "pen compatibility", "elastic closure",
                "ribbon marker", "back pocket utility",
            ],
        },
    },

    # -------------------------------------------------------
    # 9. FOOD & BEVERAGES
    # -------------------------------------------------------
    "food_beverages": {
        "coffee_tea": {
            "brands": [
                "Nespresso", "Illy", "Lavazza", "Peet's Coffee", "Starbucks",
                "Tim Hortons", "Twinings", "Celestial Seasonings", "Lipton",
                "Dilmah", "Harney & Sons", "Fortnum & Mason", "Ahmad Tea",
                "Death Wish Coffee", "Blue Bottle",
            ],
            "name_parts": [
                "Espresso", "Lungo", "Americano", "Blend", "Reserve",
                "Single Origin", "Dark Roast", "Medium Roast", "Light Roast",
                "Infusion", "Imperial", "Classic", "Organic", "Premium",
                "Signature",
            ],
            "features": [
                "aroma complexity", "flavor balance", "acidity level",
                "bitterness", "aftertaste quality", "sourcing transparency",
                "packaging freshness seal", "grind consistency",
                "certifications (organic/fair-trade)",
            ],
        },
        "snacks": {
            "brands": [
                "Lay's", "Pringles", "Doritos", "Cheetos", "Haribo",
                "Kinder", "Ferrero", "Lindt", "Godiva", "Cadbury",
                "Oreo", "Ritz", "Kind Bar", "RxBar", "Clif Bar",
            ],
            "name_parts": [
                "Crunchy", "Baked", "Original", "Spicy", "BBQ",
                "Cheese", "Salted", "Dark", "Caramel", "Peanut",
                "Almond", "Coconut", "Mint", "Hazelnut", "Honey",
            ],
            "features": [
                "crunchiness", "flavor intensity", "sweetness level",
                "after-taste", "portion size", "ingredient quality",
                "packaging resealability", "calorie value",
                "allergy-friendliness",
            ],
        },
        "supplements": {
            "brands": [
                "Optimum Nutrition", "MyProtein", "GNC", "BSN",
                "MuscleTech", "Dymatize", "SciSparc", "NOW Foods",
                "Garden of Life", "Cellucor", "Scivation", "BPI Sports",
            ],
            "name_parts": [
                "Whey", "Creatine", "BCAA", "Pre-Workout", "Recovery",
                "Mass Gainer", "Protein", "Essential", "Gold Standard",
                "Isolate", "Hydro", "Casein", "Multivitamin", "Omega",
                "Collagen",
            ],
            "features": [
                "mixability", "flavor accuracy", "protein content per serving",
                "sugar content", "amino acid profile", "digestibility",
                "third-party testing", "value per serving",
                "presence of artificial additives",
            ],
        },
    },

    # -------------------------------------------------------
    # 10. TOYS & KIDS
    # -------------------------------------------------------
    "toys_kids": {
        "educational_toys": {
            "brands": [
                "LEGO", "Fisher-Price", "Melissa & Doug", "Learning Resources",
                "LeapFrog", "VTech", "Montessori", "Ravensburger",
                "Thames & Kosmos", "Klutz", "National Geographic",
                "Educational Insights",
            ],
            "name_parts": [
                "Builder", "Explorer", "Discover", "Create", "Learn",
                "Think", "Science", "Math", "Art", "Nature",
                "Space", "Code", "Puzzle", "STEM", "Logic",
            ],
            "features": [
                "educational value", "age appropriateness", "durability",
                "engagement level", "ease of assembly", "creativity stimulation",
                "safety certifications", "parent involvement required",
                "replayability",
            ],
        },
        "action_figures": {
            "brands": [
                "Hasbro", "Mattel", "NECA", "McFarlane Toys", "Funko",
                "Bandai", "Tamashii Nations", "Hot Toys", "Mezco",
                "Diamond Select", "LEGO", "Spin Master",
            ],
            "name_parts": [
                "Ultimate", "Deluxe", "Collector", "Articulated", "Battle",
                "Classic", "Retro", "Premium", "Legends", "Origins",
                "Mega", "Giant", "Micro", "Elite", "Alpha",
            ],
            "features": [
                "paint quality", "articulation range", "accessory count",
                "sculpt accuracy", "scale consistency", "packaging quality",
                "character likeness", "display stability", "value for collectors",
            ],
        },
        "board_games": {
            "brands": [
                "Hasbro", "Mattel", "Asmodee", "Fantasy Flight Games",
                "Days of Wonder", "Rio Grande", "Z-Man Games",
                "Stonemaier Games", "Catan Studio", "Ravensburger",
            ],
            "name_parts": [
                "Quest", "Empire", "Chronicles", "Dynasty", "Alliance",
                "Dungeon", "Kingdom", "Legacy", "Battle", "Strategy",
                "Survival", "Adventure", "Mystery", "Classic", "Challenge",
            ],
            "features": [
                "rule complexity", "replayability", "component quality",
                "game duration balance", "player interaction",
                "artwork quality", "learning curve", "player count flexibility",
                "storage solution",
            ],
        },
    },

    # -------------------------------------------------------
    # 11. AUTOMOTIVE ACCESSORIES
    # -------------------------------------------------------
    "automotive": {
        "car_electronics": {
            "brands": [
                "Pioneer", "Kenwood", "Sony", "Alpine", "JVC",
                "Garmin", "TomTom", "BlackVue", "Nextbase", "Vantrue",
                "Viofo", "Waze", "Escort", "Whistler",
            ],
            "name_parts": [
                "Connect", "Navigate", "Vision", "Drive", "Track",
                "Dash", "Audio", "Display", "Link", "Cam",
                "Alert", "Smart", "Boost", "GPS", "Stereo",
            ],
            "features": [
                "screen clarity", "GPS map accuracy", "voice control quality",
                "Bluetooth stability", "installation ease", "night vision quality",
                "parking mode", "build quality", "app integration",
                "audio output power",
            ],
        },
        "car_care": {
            "brands": [
                "Meguiar's", "Armor All", "Mothers", "Chemical Guys",
                "Turtle Wax", "Rain-X", "3M", "Adam's Polishes",
                "Sonax", "AutoGlym",
            ],
            "name_parts": [
                "Shield", "Gloss", "Deep", "Quick", "Protect",
                "Ceramic", "Hybrid", "Spray", "Detailing", "Polish",
                "Wax", "Foam", "Cleanse", "Restore", "Seal",
            ],
            "features": [
                "shine depth", "water beading", "application ease",
                "durability of protection", "scratch resistance",
                "clearcoat safety", "product smell", "residue removal",
                "UV protection",
            ],
        },
        "car_accessories": {
            "brands": [
                "Thule", "Yakima", "WeatherTech", "BDK", "FH Group",
                "Michelin", "Bosch", "Autolite", "Covercraft",
                "Husky Liners",
            ],
            "name_parts": [
                "Cargo", "Rack", "Liner", "Cover", "Mount",
                "Holder", "Organizer", "Sunshade", "Floor", "Mat",
                "Trunk", "Roof", "Hitch", "Cushion", "Wrap",
            ],
            "features": [
                "fit accuracy", "installation ease", "material durability",
                "load capacity", "weather resistance", "aesthetic integration",
                "vibration noise", "portability",
            ],
        },
    },

    # -------------------------------------------------------
    # 12. HEALTH & WELLNESS
    # -------------------------------------------------------
    "health_wellness": {
        "medical_devices": {
            "brands": [
                "Omron", "Withings", "Beurer", "A&D Medical", "Philips",
                "iHealth", "Braun", "Welch Allyn", "Contour",
                "Dexcom",
            ],
            "name_parts": [
                "Smart", "Precision", "Digital", "Wireless", "Connect",
                "Monitor", "Comfort", "Track", "Check", "Sense",
                "Plus", "Pro", "Ultra", "Evo", "Air",
            ],
            "features": [
                "measurement accuracy", "cuff comfort", "reading consistency",
                "app synchronization", "data export quality",
                "battery life", "alert features", "display clarity",
                "multi-user support",
            ],
        },
        "vitamins_supplements": {
            "brands": [
                "Centrum", "Nature Made", "Garden of Life", "Solgar",
                "NOW Foods", "Thorne", "Pure Encapsulations", "Ritual",
                "Olly", "Gaia Herbs", "Vitacost", "Kirkland",
            ],
            "name_parts": [
                "Daily", "Boost", "Complex", "Essential", "Immune",
                "Energy", "Sleep", "Calm", "Gummy", "Probiotic",
                "Omega-3", "Vitamin", "Mineral", "Multi", "Premium",
            ],
            "features": [
                "bioavailability", "capsule size", "taste (chewable)",
                "third-party certification", "ingredient sourcing",
                "absence of fillers", "dosage accuracy", "price per serving",
                "allergen information",
            ],
        },
        "yoga_recovery": {
            "brands": [
                "Manduka", "Lululemon", "Gaiam", "Liforme", "Jade Yoga",
                "Theragun", "Hyperice", "TriggerPoint", "Foam Roller Factory",
                "Mobility Tools", "Rumble Roller",
            ],
            "name_parts": [
                "PRO", "Cork", "Align", "Rest", "Restore", "Deep",
                "Flex", "Rebound", "Release", "Calm", "Rejuvenate",
                "Balance", "Therapy", "Relief", "Recover",
            ],
            "features": [
                "grip quality", "cushioning thickness", "durability",
                "eco-friendliness", "vibration amplitude", "heat depth",
                "portability", "noise level", "pressure adjustment",
                "attachment variety",
            ],
        },
    },

    # -------------------------------------------------------
    # 13. HOME DÉCOR & FURNITURE
    # -------------------------------------------------------
    "home_decor": {
        "furniture": {
            "brands": [
                "IKEA", "Wayfair", "West Elm", "Pottery Barn",
                "Crate & Barrel", "Ashley Furniture", "Restoration Hardware",
                "Article", "Floyd", "Castlery", "Nathan James",
            ],
            "name_parts": [
                "Nordic", "Modern", "Classic", "Rustic", "Industrial",
                "Minimalist", "Scandi", "Artisan", "Compact", "Modular",
                "Floating", "Convertible", "Adjustable", "Streamlined",
                "Heritage",
            ],
            "features": [
                "assembly difficulty", "material finish quality",
                "structural stability", "weight capacity",
                "instruction clarity", "dimensions accuracy",
                "surface scratch resistance", "hardware quality",
                "aesthetic coherence",
            ],
        },
        "lighting": {
            "brands": [
                "Philips Hue", "LIFX", "Nanoleaf", "Govee", "Wyze",
                "TP-Link Kasa", "IKEA Tradfri", "Lutron", "Sengled",
                "Yeelight", "Leviton",
            ],
            "name_parts": [
                "Smart", "Bloom", "Ambiance", "Color", "Warm", "Cool",
                "Daylight", "Strip", "Gradient", "Spotlight", "Pendant",
                "Floor", "Table", "Desk", "Ceiling",
            ],
            "features": [
                "color temperature range", "brightness accuracy",
                "app responsiveness", "schedule reliability",
                "hub required or not", "voice assistant integration",
                "color rendering index", "lifespan",
            ],
        },
        "bedding_bath": {
            "brands": [
                "Brooklinen", "Parachute", "Casper", "Saatva",
                "Purple", "Buffy", "Boll & Branch", "Sobel Westex",
                "Egyptian Cotton", "Beckham Hotel Collection",
            ],
            "name_parts": [
                "Luxe", "Classic", "Organic", "Cooling", "Weighted",
                "Percale", "Sateen", "Linen", "Waffle", "Bamboo",
                "Fleece", "Microfiber", "Egyptian", "Tencel", "Cozy",
            ],
            "features": [
                "thread count feel", "cooling properties",
                "washing durability", "color retention",
                "softness level", "breathability", "weight comfort",
                "wrinkle resistance", "hypoallergenic quality",
            ],
        },
    },

    # -------------------------------------------------------
    # 14. OFFICE & PRODUCTIVITY
    # -------------------------------------------------------
    "office": {
        "office_furniture": {
            "brands": [
                "Herman Miller", "Steelcase", "Flexispot", "Uplift Desk",
                "Autonomous", "Ikea", "Humanscale", "Haworth",
                "VariDesk", "Ergotron",
            ],
            "name_parts": [
                "Ergonomic", "Height-Adjust", "Standing", "Fixed",
                "L-Shaped", "Corner", "Executive", "Compact",
                "Pneumatic", "Electric", "Manual", "Sit-Stand",
                "Extra Wide", "Dual Monitor", "Modular",
            ],
            "features": [
                "lumbar support", "seat depth adjustment",
                "armrest configurability", "desk stability at height",
                "cable management system", "surface durability",
                "motor noise level", "weight capacity", "assembly ease",
            ],
        },
        "office_supplies": {
            "brands": [
                "Staples", "Post-it", "Avery", "Scotch", "Swingline",
                "Fellowes", "Quartet", "Kensington", "Logitech",
                "BIC", "Zebra", "Pilot",
            ],
            "name_parts": [
                "Pro", "Ultra", "Classic", "Heavy Duty", "Compact",
                "Ergonomic", "Smart", "Multi", "Deluxe", "Essential",
                "Premium", "Standard", "Wireless", "Desktop", "Mobile",
            ],
            "features": [
                "binding capacity", "paper jam frequency", "cut precision",
                "ink flow consistency", "adhesion strength",
                "storage capacity", "portability", "refillability",
            ],
        },
        "printers_scanners": {
            "brands": [
                "HP", "Canon", "Epson", "Brother", "Lexmark",
                "Xerox", "Ricoh", "Konica Minolta", "Samsung", "Kodak",
            ],
            "name_parts": [
                "LaserJet", "DeskJet", "PIXMA", "WorkForce", "EcoTank",
                "OfficeJet", "MFC", "ColorQube", "Phaser", "ImagesRUNNER",
                "Instant", "Tank", "Color", "Mono", "Compact",
            ],
            "features": [
                "print quality at draft", "print quality at best",
                "scan resolution", "wireless setup ease", "ADF capacity",
                "ink cost per page", "print speed (ppm)", "duplex performance",
                "app ecosystem", "toner cartridge yield",
            ],
        },
    },

    # -------------------------------------------------------
    # 15. PET SUPPLIES
    # -------------------------------------------------------
    "pet_supplies": {
        "dog_supplies": {
            "brands": [
                "Chewy", "Purina", "Royal Canin", "Hill's Science Diet",
                "Orijen", "Kong", "Ruffwear", "Kurgo", "PetSafe",
                "Nylabone", "Outward Hound", "Furbo",
            ],
            "name_parts": [
                "Pro", "Fit", "Buddy", "Patrol", "Comfort", "Play",
                "Training", "Sport", "Guard", "Smart", "Activity",
                "Travel", "Groom", "Treat", "Snuggle",
            ],
            "features": [
                "durability under chewing", "size appropriateness",
                "ingredient quality", "palatability", "odor control",
                "wash-and-dry ease", "safety certifications",
                "stimulation value", "portion control accuracy",
            ],
        },
        "cat_supplies": {
            "brands": [
                "Purina", "Royal Canin", "Whiskas", "Hill's", "Sheba",
                "Catit", "Litter-Robot", "PetFusion", "SmartyKat",
                "Feliway", "Modkat", "Hepper",
            ],
            "name_parts": [
                "Feline", "Purrfect", "Cozy", "Playful", "Senior",
                "Indoor", "Kitten", "Classic", "Luxury", "Natural",
                "Smart", "Calm", "Active", "Groom", "Comfort",
            ],
            "features": [
                "odor trapping efficiency", "litter clumping strength",
                "dust levels", "ingredient quality", "palatability",
                "washability", "scratch texture", "dental benefit",
                "calming effect",
            ],
        },
        "aquarium_supplies": {
            "brands": [
                "Fluval", "MarineLand", "API", "Aqueon", "Tetra",
                "Seachem", "Caribsea", "EHEIM", "Hygger", "Coralife",
            ],
            "name_parts": [
                "Crystal", "Aqua", "Marine", "Fresh", "Filter",
                "Pump", "Light", "Nano", "Tank", "Heater",
                "Substrate", "Planted", "Reef", "Glow", "Bio",
            ],
            "features": [
                "filtration efficiency", "noise level", "ease of cleaning",
                "flow rate adjustability", "LED spectrum quality",
                "temperature consistency", "water clarity results",
                "livestock safety",
            ],
        },
    },
}


# =========================================================
# PRODUCT ADJECTIVES — Expanded to 60+ for maximum diversity
# =========================================================
PRODUCT_ADJECTIVES = [
    # Original
    "Smart", "Premium", "Ultra", "Portable", "Compact", "Advanced",
    "Professional", "Modern", "Classic", "Dynamic", "Essential", "Wireless",
    "Eco", "Elegant", "Power", "Turbo", "Flex", "Mini", "Next-Gen",
    "Pro-Grade", "Sleek", "Silent", "Limited Edition",
    # New additions
    "Signature", "Titanium", "Crystal", "Phantom", "Stealth", "Fusion",
    "Hybrid", "Quantum", "Carbon", "Cobalt", "Arctic", "Onyx",
    "Infinity", "Zen", "Apex", "Storm", "Eclipse", "Aurora",
    "Solar", "Velocity", "Precision", "Streamlined", "Artisan",
    "Obsidian", "Sapphire", "Heritage", "Nimble", "Blaze", "Apex",
    "Summit", "Zenith", "Pinnacle", "Edge", "Vortex", "Titan",
    "Celestial", "Radiant", "Surge", "Liquid", "Aero",
]


# =========================================================
# TOPICS POOL — Expanded to 40+ diverse review topics
# =========================================================
TOPICS_POOL = [
    # Original
    "quality", "delivery", "price", "performance", "battery",
    "design", "comfort", "durability", "packaging", "value",
    "customer service", "unboxing", "instructions", "warranty",
    # New additions
    "ease of use", "setup experience", "reliability", "noise level",
    "portability", "connectivity", "compatibility", "software updates",
    "resale value", "after-sales support", "environmental impact",
    "safety", "energy efficiency", "user manual clarity",
    "returns process", "tracking accuracy", "seller responsiveness",
    "payment options", "discount applied", "bundle value",
    "seasonal availability", "upgrade worthiness", "gifting suitability",
    "long-term durability", "material feel", "size accuracy",
]
