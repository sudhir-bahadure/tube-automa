import requests
import random

def get_fact():
    # Fallback facts if API fails
    facts = [
        "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.",
        "Octopuses have three hearts. Two pump blood to the gills, while the third pumps it to the rest of the body.",
        "Bananas are berries, but strawberries aren't. Botanically speaking, true berries arise from a single flower with one ovary.",
        "A day on Venus is longer than a year on Venus. It takes Venus 243 Earth days to rotate once on its axis, but only 225 Earth days to orbit the Sun.",
        "There are more trees on Earth than stars in the Milky Way. Estimates suggest 3 trillion trees vs. 100-400 billion stars.",
        "The Eiffel Tower can be 15 cm taller during the summer. Thermal expansion causes the iron structure to grow when it gets hot.",
        "Wombat poop is cube-shaped. This prevents it from rolling away and marks their territory effectively.",
        "Human teeth are the only part of the body that cannot heal themselves. They lack the cells necessary for regeneration.",
        "The shortest war in history lasted 38 to 45 minutes. It was between Britain and Zanzibar on August 27, 1896.",
        "A cloud weighs around a million tonnes. A typical cumulus cloud has a volume of about one cubic kilometer."
    ]
    
    # Try fetching from an API (e.g., UselessFacts or Ninjas)
    try:
        response = requests.get("https://uselessfacts.jsph.pl/random.json?language=en", timeout=5)
        if response.status_code == 200:
            return response.json()['text']
    except:
        pass
        
    return random.choice(facts)

def get_hashtags(category="facts"):
    # Viral hashtags for Shorts/Reels
    tags = [
        "#Shorts", "#DidYouKnow", "#Facts", "#MindBlown", "#Interesting", 
        "#Knowledge", "#Trivia", "#DailyFacts", "#Viral", "#Trending",
        "#Science", "#History", "#LifeHacks", "#LearnSomethingNew"
    ]
    recommended = random.sample(tags, 8)
    return " ".join(recommended)

def get_video_metadata():
    fact = get_fact()
    hashtags = get_hashtags()
    title = f"Did you know this? 🤯 {hashtags.split()[1]}" # Catchy title
    description = f"{fact}\n\nSubscribe for more daily facts! 🧠\n\n{hashtags}"
    
    return {
        "text": fact,
        "title": title,
        "description": description,
        "tags": hashtags
    }

if __name__ == "__main__":
    print(get_video_metadata())
