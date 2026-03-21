import random
from .catalog import CATALOG, PRODUCT_ADJECTIVES, TOPICS_POOL

def generate_product_title(category: str, subcategory: str):
    meta = CATALOG[category][subcategory]
    brand = random.choice(meta["brands"])
    part1 = random.choice(meta["name_parts"])
    part2 = random.choice(PRODUCT_ADJECTIVES)
    model = random.randint(100, 9999)

    title_patterns = [
        f"{brand} {part1} {part2} {model}",
        f"{brand} {part2} {part1} {model}",
        f"{brand} {part1} Series {model}",
        f"{brand} {part2} Edition {model}",
    ]
    return random.choice(title_patterns), brand

def generate_product_description(category: str, subcategory: str, brand: str, title: str):
    meta = CATALOG[category][subcategory]
    selected_features = random.sample(meta["features"], k=min(2, len(meta["features"])))
    feature1 = selected_features[0]
    feature2 = selected_features[1] if len(selected_features) > 1 else selected_features[0]

    sentences = [
        f"{title} by {brand} is designed for users who strongly value {feature1}.",
        f"This {subcategory.replace('_', ' ')} line up sets a new standard for {feature2}.",
        f"It is suitable for demanding routines and built to deliver reliable results under stress.",
        f"Customers continually praise its robust {feature1} and intuitive ease of use.",
        f"A magnificent choice in the {category.replace('_', ' ')} sector for advanced power-users and daily casuals alike."
    ]
    return " ".join(sentences)

def generate_topics(category: str, subcategory: str):
    feature_topics = CATALOG[category][subcategory]["features"]
    generic_topics = ["quality", "delivery", "price", "durability", "value"]
    pool = list(dict.fromkeys(feature_topics + generic_topics + TOPICS_POOL))
    return random.sample(pool, k=min(3, len(pool)))

def generate_review(sentiment: str, category: str, subcategory: str):
    features = CATALOG[category][subcategory]["features"]
    feature = random.choice(features)
    
    style = random.choice(["short", "long", "detailed", "emotional", "technical"])
    
    templates = {
        "positive": {
            "short": ["Great {feature}!", "Amazing {feature}.", "Loved the {feature}.", "Perfect {feature}.", "Five stars for {feature}."],
            "long": [
                "I have been using this for a few weeks now and the {feature} is completely outstanding. It genuinely changed how I use the product on a daily basis. I highly recommend it.",
                "After doing a lot of research, I decided to go with this one because of its {feature}. I am not disappointed at all! The {feature} exceeded my expectations significantly.",
                "This is quite possibly the best purchase I have made all year. The {feature} alone is worth the price, not to mention the overall build quality and design."
            ],
            "detailed": [
                "Let me break down why this gets 5 stars: the {feature} is remarkably consistent. Unlike other brands where the {feature} degrades over time, this one holds up well under heavy daily use.",
                "In my 3 weeks of testing, the {feature} stood out the most. The integration is seamless and the overall experience is polished. Very reliable {feature}.",
                "Pros: impeccable {feature}, sturdy build, reasonable price. Cons: None so far. The {feature} works exactly in the way advertised."
            ],
            "emotional": [
                "I am absolutely in love with this! The {feature} brings so much joy and makes my life incredibly easier. I can't imagine living without it!",
                "Wow! Just wow! The {feature} blew my mind completely! I'm so happy I bought this, it's a game changer!",
                "This makes me feel so good every time I use it. The {feature} is gorgeous and my heart just melts using it."
            ],
            "technical": [
                "From a hardware and software perspective, the {feature} leverages an optimized architecture. Excellent engineering.",
                "The {feature} shows remarkable efficiency under load testing. It allows sustained performance at peak limits without thermal throttling.",
                "Integration with the {feature} API is flawless. The telemetry data confirms that the {feature} operates within a 1% error margin under stress."
            ]
        },
        "neutral": {
            "short": ["Okay {feature}.", "Average {feature}.", "Decent {feature}.", "Not bad {feature}."],
            "long": [
                "It's an okay product but the {feature} leaves a bit to be desired. It works fine for basic tasks but struggles if you push it.",
                "I guess you get what you pay for. The {feature} is completely average. Don't expect to be blown away.",
                "Nothing special here. The {feature} is exactly as described, neither great nor terrible."
            ],
            "detailed": [
                "While the general build is okay, the {feature} feels a bit lacking in refinement. You'll notice some inconsistency when using the {feature} continuously.",
                "Testing the {feature} reveals moderate performance. It hits the baseline metrics but fails to reach the premium standard of its competitors.",
                "On paper, the {feature} looks great. In practice, it's just okay. The {feature} implementation is passable but there are better options out there."
            ],
            "emotional": [
                "I'm feeling so conflicted. The {feature} is okay, but I really wanted to love it. It just left me feeling indifferent.",
                "It's just 'meh'. I'm not angry, but the {feature} didn't spark any joy. Very underwhelming experience.",
                "To be honest, I'm slightly disappointed but not surprised. The {feature} is just barely doing its job."
            ],
            "technical": [
                "The {feature} benchmark results are strictly median. It demonstrates noticeable bottlenecks when the system is under 80% load.",
                "The architecture supporting the {feature} handles synchronous tasks fine, but asynchronous processes exhibit minor stuttering.",
                "There is a 15% variance in the {feature} output consistency. The module meets bare minimum specifications but lacks advanced optimization."
            ]
        },
        "negative": {
            "short": ["Terrible {feature}.", "Hate the {feature}.", "Awful {feature}.", "Do not buy.", "Broken {feature}."],
            "long": [
                "I am incredibly frustrated with this purchase. The {feature} broke within the first week of use, and customer support was completely unhelpful.",
                "Save your money and avoid this brand. The {feature} is wildly misrepresented in the marketing and fails to work properly most of the time.",
                "This is undeniably the worst item I've bought on this site. The {feature} is fundamentally flawed and renders the whole product practically unusable."
            ],
            "detailed": [
                "Let's talk about the {feature}. It frequently disconnects or stops functioning entirely under normal use. Moreover, the construction feels incredibly cheap.",
                "During my first day of testing, the {feature} caused the unit to shut down entirely. This is a severe defect in the design. I am returning it immediately.",
                "The major issue lies in the {feature}. Due to poor quality control, it constantly underperforms and runs dangerously hot during basic operations."
            ],
            "emotional": [
                "I am utterly devastated! I saved up for this and the {feature} is a complete disaster. It honestly ruined my week.",
                "This makes me so angry! Honestly, the {feature} is a joke. I feel totally scammed and disrespected as a customer.",
                "I could literally cry. The {feature} completely failed during an important moment. Absolutely heartbreaking product."
            ],
            "technical": [
                "Critical failure in the {feature} subsystem. We detected severe memory leaks and thermal runaway when engaged for more than 10 minutes.",
                "The algorithmic complexity of the {feature} seems poorly optimized, leading to extreme latency spikes. The hardware cannot accommodate the software overhead.",
                "Total structural failure of the {feature} component. The tolerance allows for micro-fractures under standard operational stress."
            ]
        }
    }

    text = random.choice(templates[sentiment][style]).format(feature=feature)
    
    if style in ["short", "emotional"] and random.random() < 0.2:
        text = text.lower().replace("!", "").replace(".", "")
    
    if sentiment == "positive":
        rating = random.choices([4, 5], weights=[0.4, 0.6])[0]
    elif sentiment == "neutral":
        rating = 3
    else:
        rating = random.choices([1, 2], weights=[0.6, 0.4])[0]
        
    return text, rating
