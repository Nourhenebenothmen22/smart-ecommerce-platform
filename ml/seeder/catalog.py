# =========================================================
# DATA CATALOG
# =========================================================
CATALOG = {
    "electronics": {
        "smartphones": {
            "brands": ["Apple", "Samsung", "Xiaomi", "OnePlus", "Huawei", "Google", "Oppo", "Sony", "Nokia"],
            "name_parts": ["Pro", "Max", "Lite", "Ultra", "Edge", "Plus", "Neo", "Prime", "Fold", "Flip"],
            "features": ["battery life", "camera", "screen quality", "performance", "charging speed", "build quality", "AI features"],
        },
        "laptops": {
            "brands": ["Dell", "HP", "Lenovo", "Asus", "Acer", "MSI", "Apple", "Razer", "Microsoft"],
            "name_parts": ["Book", "Air", "Pro", "Flex", "Think", "Studio", "Slim", "Core", "Zen", "Spectre"],
            "features": ["keyboard", "performance", "OLED screen", "battery life", "cooling system", "build quality", "weight"],
        },
        "tablets": {
            "brands": ["Apple", "Samsung", "Lenovo", "Huawei", "Xiaomi", "Amazon"],
            "name_parts": ["Tab", "Pad", "Air", "Mini", "Pro", "Go", "Fire"],
            "features": ["screen resolution", "battery life", "portability", "performance", "pencil support"],
        },
        "headphones": {
            "brands": ["Sony", "JBL", "Bose", "Apple", "Samsung", "Anker", "Logitech", "Sennheiser", "Audio-Technica"],
            "name_parts": ["Sound", "Beat", "Air", "Pods", "Studio", "Wave", "Tune", "Quiet", "Momentum"],
            "features": ["sound quality", "comfort", "battery life", "noise cancellation", "design", "mic quality"],
        },
        "cameras": {
            "brands": ["Canon", "Nikon", "Sony", "Fujifilm", "Panasonic", "GoPro", "DJI"],
            "name_parts": ["Shot", "Zoom", "Vision", "Capture", "Snap", "Focus", "Alpha"],
            "features": ["image quality", "zoom", "autofocus speed", "battery life", "video stabilization", "low light capability"],
        },
    },
    "beauty": {
        "skincare": {
            "brands": ["Cerave", "Vichy", "Nivea", "La Roche-Posay", "Garnier", "Bioderma", "Clinique"],
            "name_parts": ["Glow", "Hydra", "Pure", "Fresh", "Calm", "Care", "Vital", "Balance"],
            "features": ["texture", "hydration", "anti-aging", "price", "fragrance", "absorption"],
        },
        "makeup": {
            "brands": ["Maybelline", "L'Oreal", "Sephora", "NYX", "MAC", "Essence", "Fenty Beauty"],
            "name_parts": ["Color", "Shine", "Soft", "Velvet", "Matte", "Glow", "Lush", "Tint"],
            "features": ["coverage", "texture", "color palette", "durability", "pigmentation"],
        },
        "haircare": {
            "brands": ["Dove", "Pantene", "L'Oreal", "Garnier", "Elseve", "Head & Shoulders", "Kerastase"],
            "name_parts": ["Repair", "Smooth", "Silk", "Care", "Nutri", "Shine", "Volumize"],
            "features": ["fragrance", "shine effect", "texture", "effectiveness", "sulfate-free"],
        },
        "fragrance": {
            "brands": ["Dior", "Chanel", "YSL", "Armani", "Zara", "Versace", "Tom Ford", "Givenchy"],
            "name_parts": ["Bloom", "Secret", "Night", "Rose", "Fresh", "Aura", "Noir", "Oud"],
            "features": ["fragrance notes", "longevity", "bottle design", "uniqueness", "sillage"],
        },
    },
    "home_appliances": {
        "kitchen_appliances": {
            "brands": ["Philips", "Tefal", "Moulinex", "Bosch", "LG", "Samsung", "Panasonic", "KitchenAid"],
            "name_parts": ["Cook", "Chef", "Mix", "Smart", "Home", "Easy", "Blend", "Grill"],
            "features": ["power", "durability", "design", "ease of cleaning", "ease of use", "safety mechanisms"],
        },
        "cleaning_devices": {
            "brands": ["Dyson", "Philips", "Samsung", "Bosch", "Karcher", "Shark", "iRobot"],
            "name_parts": ["Clean", "Turbo", "Power", "Fresh", "Sweep", "Vac", "Bot"],
            "features": ["suction power", "durability", "battery life", "maneuverability", "smart navigation"],
        },
        "air_conditioning": {
            "brands": ["LG", "Samsung", "Gree", "Midea", "Hisense", "Daikin"],
            "name_parts": ["Cool", "Breeze", "Air", "Fresh", "Comfort", "Inverter"],
            "features": ["cooling speed", "noise level", "energy efficiency", "price", "smart controls"],
        },
    },
    "computers": {
        "desktop_pc": {
            "brands": ["Dell", "HP", "Lenovo", "Asus", "Acer", "MSI", "Corsair"],
            "name_parts": ["Tower", "Core", "Vision", "Pro", "Power", "Station", "Elite"],
            "features": ["gaming performance", "cooling", "design", "upgradeability", "price"],
        },
        "computer_accessories": {
            "brands": ["Logitech", "Razer", "Corsair", "HP", "Dell", "Asus", "Keychron"],
            "name_parts": ["Mouse", "Key", "Hub", "Link", "Pad", "Dock", "Switch"],
            "features": ["ergonomics", "comfort", "build quality", "connectivity", "price"],
        },
        "storage_devices": {
            "brands": ["Samsung", "Kingston", "SanDisk", "WD", "Seagate", "Crucial", "Corsair"],
            "name_parts": ["Drive", "Store", "Flash", "Secure", "Speed", "Vault", "NVMe"],
            "features": ["read/write speed", "storage capacity", "durability", "design", "price"],
        },
    },
    "gaming": {
        "gaming_consoles": {
            "brands": ["Sony", "Microsoft", "Nintendo", "Asus", "Valve"],
            "name_parts": ["Play", "Box", "Next", "Arena", "Game", "Zone", "Deck"],
            "features": ["performance", "exclusive games", "design", "price", "storage"],
        },
        "gaming_accessories": {
            "brands": ["Razer", "Logitech", "Corsair", "SteelSeries", "HyperX"],
            "name_parts": ["Gear", "Elite", "Pro", "Strike", "Boost", "Pulse", "Wired"],
            "features": ["comfort", "response time", "design", "durability", "price"],
        },
        "gaming_chairs": {
            "brands": ["DXRacer", "Secretlab", "Razer", "Corsair", "Asus", "Noblechairs"],
            "name_parts": ["Seat", "Comfort", "Throne", "Elite", "Pro", "Titan"],
            "features": ["lumbar support", "design", "durability", "adjustability", "material quality"],
        },
    }
}

PRODUCT_ADJECTIVES = [
    "Smart", "Premium", "Ultra", "Portable", "Compact", "Advanced",
    "Professional", "Modern", "Classic", "Dynamic", "Essential", "Wireless",
    "Eco", "Elegant", "Power", "Turbo", "Flex", "Mini", "Next-Gen", "Pro-Grade", 
    "Sleek", "Silent", "Limited Edition"
]

TOPICS_POOL = [
    "quality", "delivery", "price", "performance", "battery",
    "design", "comfort", "durability", "packaging", "value",
    "customer service", "unboxing", "instructions", "warranty"
]
