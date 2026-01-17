import random
import json

class LocalBrain:
    """
    An offline script and metadata generator that works without any APIs.
    Ensures the 'Forever Free' model by giving the system a local 'narrative logic'.
    """

    def __init__(self):
        # Library of relatable narrative patterns
        self.hooks = {
            "meme": [
                "I was today years old when I realized...",
                "Wait, tell me this hasn't happened to you...",
                "Am I the only one who thinks this is weird?",
                "The actual audacity of this situation...",
                "My brain at 3 AM is just built different."
            ],
            "curiosity": [
                "You probably think you understand this, but you don't.",
                "Everything we know about this might be a lie.",
                "Imagine for a second that reality is just a simulation.",
                "This discovery could change the history books forever.",
                "There is a hidden truth about this that no one talks about."
            ]
        }

        self.connectors = [
            "And that's when things got really strange.",
            "But here is the part that actually blows my mind.",
            "Think about it for a second.",
            "Honestly, it's just one of those things you can't explain.",
            "But wait, there's more to the story."
        ]

        self.punchlines = {
            "meme": [
                "And now I can't unsee it. Thanks for coming to my Ted Talk.",
                "Moral of the story? Don't even try. Just stay in bed.",
                "I'm not crying, you're crying. Okay, we're both crying.",
                "Anyway, that's my personality now. Hope you enjoyed it.",
                "If you relate to this, we are officially best friends."
            ],
            "curiosity": [
                "The universe is much stranger than we can imagine. Subscribe for more.",
                "Sometimes, the questions are more important than the answers.",
                "We are just scratching the surface of what's possible.",
                "What do you think? Is this real or just a glitch in the matrix?",
                "The truth is out there. We just have to look closer."
            ]
        }

    def generate_offline_script(self, topic, video_type="short", niche="curiosity"):
        """Assembles a script from local templates."""
        print(f"  [BRAIN] Generating offline script for: {topic}")
        
        niche_key = "meme" if niche == "meme" else "curiosity"
        
        hook = random.choice(self.hooks.get(niche_key))
        mid1 = random.choice(self.connectors)
        mid2 = f"When it comes to {topic}, we often overlook the obvious."
        mid3 = random.choice(self.connectors)
        punch = random.choice(self.punchlines.get(niche_key))
        
        segments = []
        texts = [hook, mid1, mid2, mid3, punch]
        
        for i, text in enumerate(texts):
            segments.append({
                "text": text,
                "visual_keywords": [topic, "abstract", "mystery"] if i % 2 == 0 else ["dark", "light", "texture"],
                "stickman_poses": ["standing normally", "standing relaxed"] if i % 2 == 0 else ["thinking", "pointing"],
                "duration_estimate": 7
            })
            
        return {
            "title": f"The Secret of {topic} Revealed!",
            "tags": [niche, "shorts", "viral", "facts"],
            "script_segments": segments
        }

    def generate_offline_title(self, topic):
        return f"Why {topic} is Actually SHOCKING! 😱"

    def generate_offline_tags(self, topic):
        return f"#shorts #{topic.replace(' ', '')} #facts #mystery #viral"

    def generate_offline_description(self, topic, title):
        return f"{title}\n\nWe dive deep into the mystery of {topic}. Watch until the end to see why this changes everything!\n\n#shorts #facts #viral\n\nDISCLAIMER: Content generated with the help of local AI logic."

local_brain = LocalBrain()
