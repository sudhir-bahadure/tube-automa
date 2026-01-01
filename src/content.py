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
    
    # Fetch 3 unique facts to make the video longer (~40s)
    facts_collection = []
    
    # Attempt to fetch 5 times to get 3 unique facts
    for _ in range(5):
        if len(facts_collection) >= 3:
            break
        try:
            response = requests.get("https://uselessfacts.jsph.pl/random.json?language=en", timeout=5)
            if response.status_code == 200:
                text = response.json()['text']
                if text not in facts_collection:
                    facts_collection.append(text)
        except:
            pass
            
    # Fallback if API fails
    if len(facts_collection) < 3:
        needed = 3 - len(facts_collection)
        facts_collection.extend(random.sample(facts, needed))
        
    # Combine with transitions
    transitions = [
        " And did you know...",
        " Here is another mind-blowing fact.",
        " Also...",
        " Listen to this.",
        " You won't believe this next one."
    ]
    
    final_script = facts_collection[0]
    for i in range(1, len(facts_collection)):
        final_script += f"{random.choice(transitions)} {facts_collection[i]}"
        
    return final_script

def get_meme_metadata():
    # Fetch multiple safe jokes for a compilation
    memes_list = []
    attempts = 0
    target_count = 5 
    
    while len(memes_list) < target_count and attempts < 15:
        attempts += 1
        try:
            r = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=5)
            if r.status_code == 200:
                data = r.json()
                setup = data['setup']
                punchline = data['punchline']
                
                # Avoid duplicates
                if not any(m['setup'] == setup for m in memes_list):
                    memes_list.append({
                        "setup": setup,
                        "punchline": punchline
                    })
        except:
            pass
            
    # Fallback if API fails completely
    if not memes_list:
        memes_list = [
            {"setup": "Why did the programmer quit his job?", "punchline": "Because he didn't get arrays."},
            {"setup": "How do you comfort a JavaScript bug?", "punchline": "You console it."},
            {"setup": "Why do Python programmers have low vision?", "punchline": "Because they don't C sharp."}
        ]

    # Combine scripts for description/tts if needed, but generator will handle individual clips
    full_script_text = " ".join([f"{m['setup']} {m['punchline']}" for m in memes_list])
    
    # Hashtags
    hashtags = "#Memes #Funny #DailyMemes #Humor #Shorts #Jokes #Compilation"
    
    return {
        "mode": "meme",
        "memes": memes_list,  # List of {setup, punchline}
        "text": full_script_text, # Legacy support
        "title": f"Daily Meme Therapy! 😂 ({len(memes_list)} Jokes)",
        "description": f"Enjoy these funny jokes!\n\n{hashtags}",
        "tags": hashtags,
        "youtube_category": "23" # Comedy
    }

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
        "tags": hashtags,
        "youtube_category": "27" # Education
    }

if __name__ == "__main__":
    print(get_video_metadata())
