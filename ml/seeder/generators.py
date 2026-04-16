"""
generators.py — Text generation engine for product titles, descriptions, and NLP review corpus.
Produces highly diverse, realistic reviews for downstream NLP/Sentiment Analysis training.
"""
import random
from .catalog import CATALOG, PRODUCT_ADJECTIVES, TOPICS_POOL


# =========================================================
# PRODUCT GENERATORS
# =========================================================

def generate_product_title(category: str, subcategory: str) -> tuple[str, str]:
    """Generate a realistic product title and return (title, brand)."""
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


def generate_product_description(category: str, subcategory: str, brand: str, title: str) -> str:
    """Generate a rich product description."""
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


def generate_topics(category: str, subcategory: str) -> list[str]:
    """Generate a list of topic labels for review analysis."""
    feature_topics = CATALOG[category][subcategory]["features"]
    generic_topics = ["quality", "delivery", "price", "durability", "value"]
    pool = list(dict.fromkeys(feature_topics + generic_topics + TOPICS_POOL))
    return random.sample(pool, k=min(3, len(pool)))


# =========================================================
# REVIEW GENERATION ENGINE — Massive NLP Corpus
# =========================================================

# --- Positive Templates (10+ per style = 50+ total) ---
_POSITIVE_TEMPLATES = {
    "short": [
        "Great {feature}!",
        "Amazing {feature}.",
        "Loved the {feature}.",
        "Perfect {feature}.",
        "Five stars for {feature}.",
        "Excellent {feature}, would buy again.",
        "Superb {feature}, absolutely love it.",
        "The {feature} alone makes it worth it!",
        "Fantastic {feature}, no complaints.",
        "Outstanding {feature}. A must-buy.",
        "Best {feature} I've ever experienced.",
        "Impressive {feature} for the price.",
    ],
    "long": [
        "I have been using this for a few weeks now and the {feature} is completely outstanding. It genuinely changed how I use the product on a daily basis. I highly recommend it to anyone looking for quality.",
        "After doing a lot of research, I decided to go with this one because of its {feature}. I am not disappointed at all! The {feature} exceeded my expectations significantly and I would purchase from this brand again.",
        "This is quite possibly the best purchase I have made all year. The {feature} alone is worth the price, not to mention the overall build quality and design which are both exceptional.",
        "I was skeptical at first, but the {feature} really won me over. After three months of daily use, it still performs like day one. The consistency is remarkable and I feel this was money well spent.",
        "My entire family uses this product now because the {feature} is just that good. We compared it with five other competing brands and none of them came close to this level of quality.",
        "Bought this as a gift for my partner and they absolutely love the {feature}. It has become their go-to daily driver. The packaging was also really nice and premium.",
        "I upgraded from the previous model and the improvement in {feature} is night and day. The engineering team clearly listened to customer feedback and delivered something truly special.",
        "Coming from a competitor's product, I was blown away by the {feature}. The attention to detail is incredible. Every interaction with this product feels smooth and intuitive.",
        "I have recommended this to at least ten friends because the {feature} is genuinely exceptional. Every single one of them has thanked me for the recommendation.",
        "The {feature} exceeded every benchmark I tested. This product punches well above its price point. If you are on the fence, just buy it, you will not regret it.",
    ],
    "detailed": [
        "Let me break down why this gets 5 stars: the {feature} is remarkably consistent. Unlike other brands where the {feature} degrades over time, this one holds up well under heavy daily use and shows no signs of wear.",
        "In my 3 weeks of testing, the {feature} stood out the most. The integration is seamless and the overall experience is polished. Very reliable {feature} that performs day after day without any issues.",
        "Pros: impeccable {feature}, sturdy build, reasonable price. Cons: None so far. The {feature} works exactly in the way advertised and the documentation is clear.",
        "I tested this side by side with three competitors. The {feature} on this model scored consistently higher across all metrics I measured. Build quality is solid, materials feel premium, and the warranty gives peace of mind.",
        "After extensive A/B testing over two weeks, the {feature} demonstrated superior performance in every category. Load times fell by 30 percent compared to the previous generation, and reliability was rock solid.",
        "From an engineering standpoint, the {feature} implementation is textbook perfect. The tolerances are tight, the finish is immaculate, and the QC clearly passed with flying colors.",
        "Day 1 vs Day 90 comparison: the {feature} has not degraded at all. I track my usage metrics weekly, and the performance curve has been flat, which is exactly what you want to see.",
        "Detailed breakdown: Setup was painless (10 minutes). The {feature} calibrated automatically. Daily use has been flawless. Customer support responded in under an hour when I had a minor question.",
        "I ran a comprehensive 30-day stress test on the {feature}. Results: zero failures, no overheating, consistent output, and power consumption within spec. This is the real deal.",
        "Comparing the spec sheet to real-world performance: the {feature} actually exceeds the manufacturer's claims. That's exceedingly rare and speaks volumes about the engineering quality.",
    ],
    "emotional": [
        "I am absolutely in love with this! The {feature} brings so much joy and makes my life incredibly easier. I can't imagine living without it at this point!",
        "Wow! Just wow! The {feature} blew my mind completely! I'm so happy I bought this, it's a total game changer for my daily routine!",
        "This makes me feel so good every time I use it. The {feature} is gorgeous and my heart just melts using it. I show it off to everyone.",
        "I literally teared up when I first experienced the {feature}. It was that beautiful and that perfect. I have never been this satisfied with a purchase.",
        "Words cannot express how happy the {feature} makes me. This is the kind of product that restores your faith in quality craftsmanship.",
        "Opening the box was a magical experience. The {feature} just radiates quality. I felt like a kid on Christmas morning, pure joy and excitement.",
        "I cannot stop talking about the {feature} to my friends and family. They must be so tired of hearing about it but I genuinely cannot help myself!",
        "This product with its incredible {feature} has genuinely improved my quality of life. That sounds dramatic but I mean it from the bottom of my heart.",
        "Every morning I wake up excited to use this. The {feature} makes even mundane tasks feel special. It has brought genuine happiness into my routine.",
        "My friends thought I was exaggerating about the {feature}. Then they tried it. Now they all own one. It really is THAT good.",
    ],
    "technical": [
        "From a hardware and software perspective, the {feature} leverages an optimized architecture. Excellent engineering decisions throughout the entire stack.",
        "The {feature} shows remarkable efficiency under load testing. It allows sustained performance at peak limits without thermal throttling or degradation.",
        "Integration with the {feature} API is flawless. The telemetry data confirms that the {feature} operates within a 1% error margin under stress.",
        "Benchmark results: the {feature} scored in the 97th percentile compared to competing solutions. Latency is consistently under 12ms, which is industry-leading.",
        "The {feature} utilizes a multi-threaded pipeline that maximizes throughput. Real-world testing confirms theoretical performance gains of 40% over the previous generation.",
        "Power efficiency metrics for the {feature} are outstanding. We measured a 22% reduction in energy consumption compared to the baseline, without any performance trade-offs.",
        "The {feature} implements hardware-accelerated processing with zero-copy memory management. The result is near-instantaneous response times even under sustained high-concurrency workloads.",
        "Signal-to-noise ratio for the {feature} measures at 118dB, which is studio-quality territory. The engineering team clearly optimized for audio fidelity at every stage of the signal chain.",
        "Thermal analysis shows the {feature} maintains sub-65C temperatures under maximum load. The vapor chamber cooling solution is exceptionally well-designed.",
        "Endurance testing over 1000 cycles shows the {feature} maintains 99.7% of original performance. The degradation curve is nearly flat, indicating exceptional component quality.",
    ],
    "comparative": [
        "I've tried many products in this category but the {feature} on this one is simply the best. Nothing else comes close in terms of quality and reliability.",
        "Switching from a competitor to this was the best decision ever. The {feature} is leagues ahead. I can never go back to what I was using before.",
        "My previous product lasted two months before the {feature} started failing. This one is still going strong after six months. The difference in quality is staggering.",
        "I bought three different brands to compare, and the {feature} on this model won hands down. The other two have already been returned.",
        "After years of settling for mediocre {feature}, I finally found the one. This product sets the standard that all others should be measured against.",
        "Price-to-performance ratio for the {feature} is unmatched. I've checked competitors at double the price and they still don't match the quality of this product.",
        "I read every review comparing {feature} across brands. This one consistently comes out on top, and now I understand why. The difference is immediately noticeable.",
        "My colleague recommended their brand, but after comparing the {feature} side by side, there's simply no contest. This product is objectively superior in every way.",
    ],
    "storytelling": [
        "I was ready to give up on finding something with good {feature} until a friend convinced me to try this. Best advice I ever took. This product is phenomenal.",
        "My old one broke right before an important deadline and I rushed to buy this as a replacement. The {feature} was so good it turned a stressful situation into a positive upgrade.",
        "I have been searching for the perfect {feature} for over two years. Dozens of products tried and returned. This is the one that finally made me stop searching.",
        "During my vacation, the {feature} performed flawlessly in extreme conditions. Heat, humidity, dust, nothing phased it. It became the MVP of my entire trip.",
        "When I first unboxed this, I was worried it wouldn't live up to the hype. Three seconds after powering on, the {feature} immediately told me this was going to be special.",
        "I accidentally left this running overnight. Not only did the {feature} handle it perfectly, but I realized just how reliable and well-engineered this product truly is.",
        "My grandmother needed something with reliable {feature} and this was perfect. She uses it every day without any issues. If my 78-year-old grandma can use it, anyone can.",
        "A photographer friend borrowed this to test the {feature} for a professional shoot. They ordered their own within the hour. That says everything you need to know.",
    ],
}

# --- Neutral Templates (8+ per style = 50+ total) ---
_NEUTRAL_TEMPLATES = {
    "short": [
        "Okay {feature}.",
        "Average {feature}.",
        "Decent {feature}.",
        "Not bad {feature}.",
        "The {feature} is acceptable.",
        "Fair {feature}, nothing special.",
        "Mediocre {feature} for the price.",
        "It works. {feature} is fine.",
        "Standard {feature}, nothing exciting.",
        "The {feature} meets basic expectations.",
        "Passable {feature}. Gets the job done.",
        "The {feature} is just okay, honestly.",
    ],
    "long": [
        "It's an okay product but the {feature} leaves a bit to be desired. It works fine for basic tasks but struggles if you push it past casual use.",
        "I guess you get what you pay for. The {feature} is completely average. Don't expect to be blown away but it won't disappoint either.",
        "Nothing special here. The {feature} is exactly as described, neither great nor terrible. It does what it claims and nothing more.",
        "The {feature} is functional but uninspiring. I was hoping for something more given the marketing promises, but it's still a usable product overall.",
        "After using it for a month, the {feature} is holding up, but I can see some areas where the quality could be better. It's a solid B-minus product.",
        "Honestly, the {feature} is mid-range at best. It performs adequately for everyday tasks but don't expect miracles. Good enough for casual users.",
        "I have mixed feelings about the {feature}. Some days it impresses me, other days it feels sluggish. Consistency is the main issue here.",
        "The {feature} wasn't as impressive as the reviews led me to believe, but it's not bad either. It falls squarely in the 'acceptable' category.",
        "For occasional use, the {feature} is perfectly adequate. But if you're a power user who needs top-tier performance, you might want to look elsewhere.",
        "I wouldn't call the {feature} good or bad. It simply exists and does its job without either delighting or frustrating me. It's the definition of average.",
    ],
    "detailed": [
        "While the general build is okay, the {feature} feels a bit lacking in refinement. You'll notice some inconsistency when using the {feature} continuously over extended periods.",
        "Testing the {feature} reveals moderate performance. It hits the baseline metrics but fails to reach the premium standard of its competitors in the same price bracket.",
        "On paper, the {feature} looks great. In practice, it's just okay. The {feature} implementation is passable but there are better options out there if you're willing to pay more.",
        "My testing shows the {feature} performs within spec but never exceeds it. You get exactly what's advertised, which can be viewed positively or negatively depending on expectations.",
        "Compared to 2024 models, the {feature} shows a marginal improvement of about 8 percent. That's not revolutionary but it's not stagnant either. Incremental progress at best.",
        "The {feature} passed all my basic tests but failed to impress in advanced scenarios. For 80% of users this will be perfectly fine, but enthusiasts will want more.",
        "Durability test after 60 days: the {feature} shows normal wear patterns. Nothing alarming, but nothing that suggests exceptional build quality either. Right on the curve.",
        "Setup was straightforward and the {feature} worked as expected out of the box. No configuration issues, but also no 'wow' moments. A very by-the-numbers experience.",
        "I compared the {feature} across three price tiers. This product sits exactly where its price suggests it should: adequate quality with reasonable compromises.",
        "Temperature readings during peak {feature} usage: 72C, which is within acceptable limits but warmer than I'd prefer. The cooling solution is functional but not exceptional.",
    ],
    "emotional": [
        "I'm feeling so conflicted. The {feature} is okay, but I really wanted to love it. It just left me feeling indifferent about the whole purchase.",
        "It's just 'meh'. I'm not angry, but the {feature} didn't spark any joy. Very underwhelming experience compared to what I was hoping for.",
        "To be honest, I'm slightly disappointed but not surprised. The {feature} is just barely doing its job and nothing more.",
        "I neither love nor hate the {feature}. It exists in this strange space where I can't muster any strong feelings about it one way or the other.",
        "I keep trying to be excited about the {feature} but it just won't happen. It's functional and that's the nicest thing I can say about it.",
        "My friends asked me if I'd recommend it and I just shrugged. The {feature} is not bad enough to warn against, but not good enough to enthusiastically endorse.",
        "Some days the {feature} surprises me in a good way, and I think maybe I was wrong. Then the next day it reverts to being unremarkable. It's exhausting.",
        "I genuinely tried to love this product for its {feature}. But after two months, I feel nothing. It's like dating someone who's nice but boring.",
    ],
    "technical": [
        "The {feature} benchmark results are strictly median. It demonstrates noticeable bottlenecks when the system is under 80% load.",
        "The architecture supporting the {feature} handles synchronous tasks fine, but asynchronous processes exhibit minor stuttering under concurrent workloads.",
        "There is a 15% variance in the {feature} output consistency. The module meets bare minimum specifications but lacks advanced optimization.",
        "Power draw for the {feature} is acceptable at 45W under load. Not the most efficient in its class, but not egregiously wasteful either.",
        "I/O throughput for the {feature} averages 380 MB/s sequential. That's within published spec but well below what competing solutions achieve.",
        "The {feature} shows standard deviation of 3.2ms in response time. Acceptable for consumer use but would not meet enterprise SLA requirements.",
        "Cache hit ratios for the {feature} hover around 78%. Decent, but the prefetch algorithm could be significantly more intelligent.",
        "The {feature} firmware appears stable with no crashes in 30 days, but it lacks the polish and optimization of more mature competing solutions.",
    ],
    "comparative": [
        "Compared to what I had before, the {feature} is roughly the same. Not better, not worse, just different in subtle ways that don't really matter.",
        "I tried a competitor's product first and the {feature} was about the same quality. At this price point, they're all pretty interchangeable honestly.",
        "My friend has a similar product and their {feature} is slightly better, but not enough to justify returning this one. The difference is marginal.",
        "Looking at the market, the {feature} sits right in the middle of the pack. You can pay more for better or less for worse. This is the safe choice.",
        "I've owned three products in this category. The {feature} on this one ranks second. Not the best, not the worst. Just solidly in the middle.",
        "The {feature} is comparable to products that cost 20% less, which makes the value proposition questionable. You're paying a small premium for the brand name.",
    ],
}

# --- Negative Templates (10+ per style = 60+ total) ---
_NEGATIVE_TEMPLATES = {
    "short": [
        "Terrible {feature}.",
        "Hate the {feature}.",
        "Awful {feature}.",
        "Do not buy.",
        "Broken {feature}.",
        "Worst {feature} ever.",
        "Complete waste of money.",
        "The {feature} is garbage.",
        "Extremely disappointing {feature}.",
        "Regret buying this. {feature} is bad.",
        "Absolute junk. {feature} failed fast.",
        "Zero stars if I could. {feature} is trash.",
    ],
    "long": [
        "I am incredibly frustrated with this purchase. The {feature} broke within the first week of use, and customer support was completely unhelpful and dismissive of my concerns.",
        "Save your money and avoid this brand entirely. The {feature} is wildly misrepresented in the marketing and fails to work properly most of the time.",
        "This is undeniably the worst item I've bought on this site. The {feature} is fundamentally flawed and renders the whole product practically unusable.",
        "I tried to give this a fair chance but the {feature} kept deteriorating with each passing day. By week three it was essentially non-functional. Total waste of money.",
        "The {feature} worked for exactly four days before showing major problems. At this price point, that level of reliability is completely unacceptable and frankly insulting.",
        "I returned this after a week because the {feature} was so poor. The return process was also a nightmare. This company clearly does not care about customer satisfaction.",
        "Everyone in my household has complained about the {feature}. It's loud, inefficient, and unreliable. I genuinely feel scammed by the marketing materials.",
        "I wish I had read more reviews before buying. The {feature} issues that others mentioned are absolutely real and even worse than described. Avoid at all costs.",
        "This product looks great in photos but the {feature} is atrocious in person. The build quality is cheap and the performance is embarrassingly poor.",
        "After three months of giving it every chance, I can confidently say the {feature} is the worst I have ever encountered. I am returning this and will never buy from this brand again.",
    ],
    "detailed": [
        "Let's talk about the {feature}. It frequently disconnects or stops functioning entirely under normal use. Moreover, the construction feels incredibly cheap and flimsy.",
        "During my first day of testing, the {feature} caused the unit to shut down entirely. This is a severe defect in the design. I am returning it immediately for a full refund.",
        "The major issue lies in the {feature}. Due to poor quality control, it constantly underperforms and runs dangerously hot during basic operations that should not be taxing.",
        "I documented every failure: Day 1 - {feature} glitched twice. Day 3 - intermittent shutdowns. Day 5 - persistent overheating. Day 7 - completely dead. Unacceptable quality control.",
        "Teardown analysis reveals the {feature} uses inferior components compared to what the marketing suggests. The PCB layout is poorly optimized and the soldering quality is substandard.",
        "Real-world performance of the {feature} falls 45% below advertised specifications. I ran standardized tests on three units and all showed the same significant underperformance.",
        "The instructions claim the {feature} will last 500+ hours. Mine failed at 73 hours. I contacted support who blamed my usage. This is clearly a manufacturing defect.",
        "I tested the {feature} across different conditions: indoor, outdoor, varying temperatures. It failed consistently in every scenario. The engineering is fundamentally flawed.",
        "Customer service acknowledged the {feature} issue but offered no recall or replacement. Their suggested workaround amounts to not using the product's main selling point.",
        "The {feature} exhibits a known design flaw where the internal mechanism loosens over time. A class-action lawsuit is apparently being discussed in consumer forums.",
    ],
    "emotional": [
        "I am utterly devastated! I saved up for this and the {feature} is a complete disaster. It honestly ruined my week and wasted months of saving.",
        "This makes me so angry! Honestly, the {feature} is a joke. I feel totally scammed and disrespected as a customer who trusted this brand.",
        "I could literally cry. The {feature} completely failed during an important moment. Absolutely heartbreaking product that let me down when I needed it most.",
        "I feel betrayed by this brand. The {feature} was the reason I chose this over competitors and it turned out to be the worst part of the entire product.",
        "This ruined an important event for me because the {feature} died at the worst possible moment. I am angry, disappointed, and honestly a little heartbroken.",
        "I am so frustrated I can barely type this review. The {feature} is an absolute nightmare and the company clearly does not care about the people buying their products.",
        "The {feature} made me lose trust in online shopping. How can something so expensive be this terrible? I feel robbed and humiliated for recommending this to friends.",
        "I genuinely want to throw this away. The {feature} has caused me nothing but stress and frustration since day one. Worst purchase of my entire life.",
        "My disappointment is immeasurable and my day is ruined. The {feature} is catastrophically bad. I expected so much more from a brand with this reputation.",
        "As someone who researches products extensively, I am shocked at how bad the {feature} is. I feel like every positive review must have been paid for.",
    ],
    "technical": [
        "Critical failure in the {feature} subsystem. We detected severe memory leaks and thermal runaway when engaged for more than 10 minutes of continuous use.",
        "The algorithmic complexity of the {feature} seems poorly optimized, leading to extreme latency spikes. The hardware cannot accommodate the software overhead at all.",
        "Total structural failure of the {feature} component. The tolerance allows for micro-fractures under standard operational stress, which is a fundamental engineering oversight.",
        "Oscilloscope analysis of the {feature} reveals significant signal degradation: 22dB loss at the output stage. This indicates substandard capacitors in the power delivery circuit.",
        "The {feature} firmware contains critical bugs: buffer overflows at high input rates, memory not freed after task completion, and race conditions in the multithreaded handler.",
        "Thermal imaging of the {feature} shows localized hotspots exceeding 95C. This is dangerously close to the component's absolute maximum rating and will cause premature failure.",
        "Failure mode analysis: the {feature} exhibits a MTBF of approximately 200 hours, which is roughly 4x lower than the industry standard for products at this price point.",
        "The {feature} power consumption spikes to 3x the rated value during burst operations. The power supply cannot handle these transients, causing system instability.",
        "Wireless {feature} testing shows a 35% packet loss rate at just 3 meters distance. The antenna design is clearly inadequate for even basic indoor use cases.",
        "The {feature} API response times average 890ms, which is completely unacceptable for real-time applications. The backend architecture appears to be single-threaded.",
    ],
    "comparative": [
        "My previous product's {feature} was infinitely better than this. I downgraded by switching to this brand and I deeply regret the decision.",
        "My friend's budget alternative has a better {feature} than this supposedly premium product. The price difference is a total ripoff.",
        "I tested this against the cheapest competitor and the {feature} was worse. Let that sink in: the cheapest option outperforms this more expensive product.",
        "After using a competitor's product for a year with zero issues, this product's {feature} failed in under a month. The quality gap is enormous.",
        "Every single competing product in this price range has better {feature}. I checked extensively after purchasing. This is objectively the worst option available.",
        "I'm going back to my old product because the {feature} was actually better despite being three years older. That tells you everything about this product's quality.",
    ],
    "storytelling": [
        "I bought this for a family road trip. The {feature} died two hours in, leaving everyone stranded without the functionality we counted on. Worst timing possible.",
        "I gave this as a birthday present and the {feature} broke during the party. I have never been so embarrassed. The recipient tried to be polite but I could see the disappointment.",
        "Ordered this for a work project deadline. The {feature} failed during my presentation to the client. I lost the contract and I blame this terrible product entirely.",
        "My old one lasted five years. This replacement with its terrible {feature} lasted five weeks. The decline in quality over the years is genuinely alarming.",
        "I trusted the five-star reviews. The {feature} proved all the one-star reviews right. Those five stars were obviously fake or paid. Real users know this is garbage.",
        "The delivery guy literally apologized when he saw what I ordered because he said he's seen too many returns of this model. The {feature} confirmed his warning.",
    ],
}

# Combine all templates into the main structure
_ALL_TEMPLATES = {
    "positive": _POSITIVE_TEMPLATES,
    "neutral": _NEUTRAL_TEMPLATES,
    "negative": _NEGATIVE_TEMPLATES,
}

# All available styles
_ALL_STYLES = ["short", "long", "detailed", "emotional", "technical", "comparative", "storytelling"]


# =========================================================
# REVIEW TEXT POST-PROCESSING (Natural Variation)
# =========================================================

_TYPO_WORDS = {
    "the": ["teh", "th", "hte"],
    "this": ["thsi", "ths"],
    "that": ["taht", "tht"],
    "and": ["adn", "nad"],
    "with": ["wiht", "wth"],
    "have": ["hav", "ahve"],
    "really": ["realy", "relly"],
    "great": ["greta", "graet"],
    "good": ["godo", "god"],
    "product": ["prodcut", "produkt"],
}

_FILLER_PHRASES = [
    "You know, ", "To be honest, ", "I mean, ", "Like, ",
    "Honestly, ", "Tbh, ", "Look, ", "So basically, ",
    "I gotta say, ", "For real though, ",
]

_EMOJI_POSITIVE = ["😍", "🔥", "💯", "👌", "❤️", "✨", "🙌", "👏", "⭐", "💪"]
_EMOJI_NEGATIVE = ["😡", "💀", "👎", "😤", "🤬", "😢", "💔", "🚫", "⚠️", "🗑️"]
_EMOJI_NEUTRAL = ["🤷", "😐", "🤔", "⚖️", "➡️"]


def _apply_natural_variation(text: str, sentiment: str) -> str:
    """Apply random post-processing to make reviews feel more organic and varied."""
    # 8% chance of adding a typo
    if random.random() < 0.08:
        for word, typos in _TYPO_WORDS.items():
            if f" {word} " in text.lower():
                text = text.replace(f" {word} ", f" {random.choice(typos)} ", 1)
                break

    # 12% chance of adding a conversational filler at the start
    if random.random() < 0.12:
        text = random.choice(_FILLER_PHRASES) + text[0].lower() + text[1:]

    # 10% chance of adding emoji
    if random.random() < 0.10:
        if sentiment == "positive":
            text += " " + random.choice(_EMOJI_POSITIVE)
        elif sentiment == "negative":
            text += " " + random.choice(_EMOJI_NEGATIVE)
        else:
            text += " " + random.choice(_EMOJI_NEUTRAL)

    # 5% chance of ALL CAPS for emotional emphasis
    if random.random() < 0.05:
        words = text.split()
        if len(words) > 3:
            idx = random.randint(0, len(words) - 1)
            words[idx] = words[idx].upper()
            text = " ".join(words)

    # 6% chance of adding extra punctuation
    if random.random() < 0.06:
        text = text.rstrip(".")
        if sentiment == "positive":
            text += random.choice(["!!!", "!!", "!!!!!"])
        elif sentiment == "negative":
            text += random.choice(["...", "!!", "!?!"])
        else:
            text += random.choice(["...", ".", "..."])

    # 4% chance of lowercase everything (lazy typing)
    if random.random() < 0.04:
        text = text.lower()

    return text


def generate_review(sentiment: str, category: str, subcategory: str) -> tuple[str, int]:
    """
    Generate a single review text and rating.
    
    Returns:
        (review_text, rating) — A diverse, NLP-ready review.
    """
    features = CATALOG[category][subcategory]["features"]
    feature = random.choice(features)

    # Pick a style, falling back to available ones for this sentiment
    available_styles = [s for s in _ALL_STYLES if s in _ALL_TEMPLATES[sentiment]]
    style = random.choice(available_styles)

    templates = _ALL_TEMPLATES[sentiment][style]
    text = random.choice(templates).format(feature=feature)

    # Apply natural variation for realistic NLP training data
    text = _apply_natural_variation(text, sentiment)

    # Multi-sentence composition: 15% chance of combining two templates
    if random.random() < 0.15 and style not in ["short"]:
        feature2 = random.choice(features)
        extra_style = random.choice(available_styles)
        extra_templates = _ALL_TEMPLATES[sentiment][extra_style]
        extra_text = random.choice(extra_templates).format(feature=feature2)
        text = text.rstrip(".!") + ". " + extra_text

    # Assign rating
    if sentiment == "positive":
        rating = random.choices([4, 5], weights=[0.35, 0.65])[0]
    elif sentiment == "neutral":
        rating = random.choices([2, 3, 4], weights=[0.15, 0.70, 0.15])[0]
    else:
        rating = random.choices([1, 2], weights=[0.65, 0.35])[0]

    return text, rating
