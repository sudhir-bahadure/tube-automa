"""
YPP-Safe Script Template System
Generates analytical, interpretive scripts that comply with YouTube Partner Program requirements
"""

import random

# ============================================================================
# YPP-COMPLIANT SCRIPT TEMPLATE
# ============================================================================

# Hook Templates (Professional/High-Impact)
HOOK_TEMPLATES = {
    "curiosity": [
        "Everyone is talking about {topic}, but they missed the most important detail...",
        "What if I told you that {topic} is about to change everything you know about tech?",
        "There's a secret about {topic} that most people aren't ready to hear."
    ],
    "fomo": [
        "If you're not using {topic} yet, you're already falling behind in the AI race.",
        "The window for mastering {topic} is closing fast. Here's what you need to know.",
        "While everyone else is sleeping, the pro's are moving everything to {topic}."
    ],
    "authority": [
        "We analyzed the latest data on {topic}, and here's the definitive guide.",
        "After 100 hours of testing {topic}, we've uncovered its true potential.",
        "As an AI analyst, I've seen many trends, but {topic} is in a league of its own."
    ],
    "part_2": [
        "We're back with Part 2 of our {topic} breakdown, and the updates are huge.",
        "The story of {topic} is evolving fast. Here's the latest update to our deep dive.",
        "Continuing our series on {topic}, we're looking at the newest breakthroughs."
    ]
}

# Reasoning phrases that MUST appear every 60-90 seconds
REASONING_PHRASES = [
    "This suggests that",
    "What this means is",
    "This challenges the assumption that",
    "From a modern perspective",
    "The significance of this is",
    "This demonstrates that",
    "When we examine this closely",
    "What makes this important is",
    "This reveals that",
    "The implication here is",
    "This fundamentally changes",
    "What we learn from this is",
    "This helps us understand"
]

# Template for each segment type
YPP_TEMPLATES = {
    "opening": [
        "What makes {topic} important is not just {aspect}, but how it {significance}. In this video, I will explain {core_insight}.",
        "The significance of {topic} goes beyond {common_fact}. What makes this truly important is {deeper_meaning}. Today, we'll explore {focus}.",
        "{topic} represents more than {surface_level}. This suggests that {interpretation}. Let's examine {analytical_focus}."
    ],
    
    "context": [
        "The commonly known facts about {topic} include {fact1} and {fact2}. However, these details alone do not explain {key_question}.",
        "When most people think of {topic}, they focus on {common_knowledge}. But this overlooks {missing_element}.",
        "Historical records show that {topic} involved {facts}. What this means is {interpretation}."
    ],
    
    "interpretation": [
        "What this suggests is {insight}. This matters because {implication}.",
        "This reveals that {discovery}. The significance of this is {importance}.",
        "When we examine this closely, we find that {analysis}. This demonstrates that {conclusion}."
    ],
    
    "challenge": [
        "For a long time, it was assumed that {old_belief}. But evidence from {topic} challenges this assumption by showing {new_understanding}.",
        "Traditional views held that {conventional_wisdom}. However, {topic} demonstrates that {contrary_evidence}.",
        "The conventional interpretation suggested {old_view}. What we now understand is {revised_view}."
    ],
    
    "modern_perspective": [
        "From a modern perspective, {topic} can be understood as {modern_comparison}. In practical terms, this means {relevance}.",
        "Today, we recognize {topic} as {contemporary_understanding}. This helps us understand {modern_application}.",
        "In contemporary terms, {topic} represents {current_interpretation}. The implication here is {modern_significance}."
    ],
    
    "analysis": [
        "This is significant because {reason}. When we examine {specific_aspect}, we find that {insight}.",
        "The deeper meaning here is {interpretation}. This fundamentally changes {impact}.",
        "What makes this important is {significance}. This reveals {discovery}."
    ],
    
    "synthesis": [
        "What {topic} ultimately demonstrates is {final_insight}. This is why it remains significant in understanding {broader_field}.",
        "The key takeaway from {topic} is {conclusion}. This helps us understand {broader_context}.",
        "In summary, {topic} shows us that {synthesis}. This matters because {lasting_impact}."
    ],
    
    "identity": [
        "This channel focuses on explaining historical and scientific discoveries through structured analysis and interpretation.",
        "Our goal is to provide analytical perspectives on important discoveries, going beyond simple facts to explore deeper meanings.",
        "We examine significant topics through careful analysis, connecting historical evidence with modern understanding."
    ]
}

# ============================================================================
# INTERPRETATION GENERATORS
# ============================================================================

def extract_key_concept(text):
    """Extract main concept from text"""
    # Simple extraction - take first significant noun phrase
    words = text.split()
    if len(words) > 3:
        return " ".join(words[:3])
    return text[:50]

def generate_significance(topic):
    """Generate why topic matters"""
    templates = [
        f"challenges our understanding of ancient technology",
        f"reveals unexpected sophistication in historical knowledge",
        f"demonstrates the complexity of early scientific thinking",
        f"shows how advanced ancient civilizations were",
        f"changes how we view the development of technology"
    ]
    return random.choice(templates)

def generate_core_insight(topic):
    """Generate main analytical point"""
    templates = [
        f"why this discovery fundamentally changes our perspective",
        f"what this reveals about human innovation",
        f"how this challenges conventional historical narratives",
        f"the deeper implications of this finding",
        f"what modern science can learn from this"
    ]
    return random.choice(templates)

def generate_key_question(topic):
    """Generate analytical question"""
    templates = [
        f"why this technology emerged when it did",
        f"how this level of sophistication was achieved",
        f"what this tells us about the broader historical context",
        f"the full implications of this discovery",
        f"how this fits into our understanding of technological evolution"
    ]
    return random.choice(templates)

def generate_interpretation(fact):
    """Generate analytical interpretation from fact"""
    templates = [
        f"this reveals a fundamental shift in how we understand ancient capabilities",
        f"this demonstrates the complexity of historical technological development",
        f"this challenges the conventional view of linear progress",
        f"this suggests a deeper connection between ancient and modern science"
    ]
    return random.choice(templates)

def generate_implication(fact):
    """Generate why it matters"""
    templates = [
        f"it fundamentally changes our approach to studying ancient technology",
        f"it opens new questions about the transmission of knowledge",
        f"it provides insight into the sophistication of early civilizations",
        f"it helps us understand the evolution of scientific thinking"
    ]
    return random.choice(templates)

def generate_old_belief(topic):
    """Generate conventional wisdom to challenge"""
    templates = [
        f"ancient civilizations lacked advanced technological knowledge",
        f"sophisticated mechanisms were beyond the capabilities of early societies",
        f"modern technology represents a complete break from the past",
        f"ancient discoveries were primarily accidental rather than systematic"
    ]
    return random.choice(templates)

def generate_new_understanding(topic):
    """Generate revised understanding"""
    templates = [
        f"ancient societies possessed remarkable scientific and engineering capabilities",
        f"technological sophistication existed far earlier than previously thought",
        f"there was significant continuity between ancient and modern scientific methods",
        f"early discoveries often resulted from systematic investigation and experimentation"
    ]
    return random.choice(templates)

def generate_modern_comparison(topic):
    """Generate contemporary parallel"""
    templates = [
        f"an early form of computational thinking",
        f"a precursor to modern scientific methodology",
        f"evidence of systematic technological development",
        f"a bridge between ancient wisdom and modern science"
    ]
    return random.choice(templates)

def generate_relevance(topic):
    """Generate modern relevance"""
    templates = [
        f"we can better appreciate the long history of human innovation",
        f"we gain insight into the foundations of modern technology",
        f"we understand that scientific progress builds on ancient foundations",
        f"we recognize the continuity of human intellectual achievement"
    ]
    return random.choice(templates)

def generate_final_insight(topic):
    """Generate concluding insight"""
    templates = [
        f"human innovation and scientific thinking have deep historical roots",
        f"technological sophistication is not solely a modern phenomenon",
        f"ancient civilizations made remarkable contributions to human knowledge",
        f"the development of technology represents a continuous human endeavor"
    ]
    return random.choice(templates)

def generate_broader_field(topic):
    """Generate broader context"""
    templates = [
        f"the history of science and technology",
        f"human intellectual development",
        f"the evolution of scientific thinking",
        f"technological progress throughout history"
    ]
    return random.choice(templates)

def generate_hook(topic, is_part_2=False):
    """Generate high-impact hook"""
    if is_part_2:
        category = "part_2"
    else:
        category = random.choice(["curiosity", "fomo", "authority"])
    
    template = random.choice(HOOK_TEMPLATES[category])
    return template.format(topic=topic)

# ============================================================================
# YPP-SAFE SCRIPT GENERATOR
# ============================================================================

def generate_ypp_safe_script(topic, wikipedia_sentences=None, is_part_2=False):
    """
    Generate YPP-compliant analytical script
    
    Args:
        topic: Main topic
        wikipedia_sentences: Optional list of Wikipedia sentences
        is_part_2: Whether this is a continuation
    
    Returns:
        List of segment dictionaries with text and type
    """
    
    segments = []
    
    # AI INTEGRATION: Try to get unique insights from Gemini
    ai_insights = None
    try:
        from llm_wrapper import GeminiWrapper
        llm = GeminiWrapper()
        if llm.is_active:
             print(f"  [AI] Generating unique documentary storyboard for: {topic}")
             ai_insights = llm.generate_script(topic, mood="tech_tutorial")
    except Exception as e:
        print(f"  [AI-LONG] Storyboard failed: {e}")

    # 1. OPENING - Analytical framing (WHY, not WHAT)
    hook = ai_insights['hook'] if ai_insights else generate_hook(topic, is_part_2)
    
    opening_template = random.choice(YPP_TEMPLATES["opening"])
    opening_base = opening_template.format(
        topic=topic,
        aspect="its historical significance",
        significance=generate_significance(topic),
        core_insight=ai_insights['cta'] if ai_insights else generate_core_insight(topic),
        common_fact="being an ancient artifact",
        deeper_meaning=generate_significance(topic),
        focus=generate_core_insight(topic),
        surface_level="a historical curiosity",
        interpretation=generate_interpretation(""),
        analytical_focus=generate_core_insight(topic)
    )
    opening = f"{hook} {opening_base}"
    segments.append({"text": opening, "type": "opening", "keyword": topic})
    
    # 2. CONTEXT - Selective facts
    if wikipedia_sentences and len(wikipedia_sentences) >= 2:
        fact1 = wikipedia_sentences[0][:100]
        fact2 = wikipedia_sentences[1][:100]
    else:
        fact1 = f"its discovery in ancient times"
        fact2 = f"its complex construction"
    
    context_template = random.choice(YPP_TEMPLATES["context"])
    context = context_template.format(
        topic=topic,
        fact1=fact1,
        fact2=fact2,
        key_question=generate_key_question(topic),
        common_knowledge=f"its basic features",
        missing_element=generate_key_question(topic),
        facts=f"{fact1} and {fact2}",
        interpretation=generate_interpretation("")
    )
    segments.append({"text": context, "type": "context", "keyword": topic})
    
    # 3-6. INTERPRETATION - Multiple analytical segments
    for i in range(4):
        interp_template = random.choice(YPP_TEMPLATES["interpretation"])
        reasoning_phrase = random.choice(REASONING_PHRASES)
        
        # QUALITY REFINEMENT: Use AI script for one of the interpretations
        if ai_insights and i == 0:
            interpretation = ai_insights['script']
        else:
            interpretation = interp_template.format(
                insight=generate_interpretation(""),
                implication=generate_implication(""),
                discovery=generate_interpretation(""),
                importance=generate_implication(""),
                analysis=generate_interpretation(""),
                conclusion=generate_final_insight(topic)
            )
        
        # Ensure reasoning phrase is included
        if not any(phrase.lower() in interpretation.lower() for phrase in REASONING_PHRASES):
            interpretation = f"{reasoning_phrase} {interpretation}"
        
        segments.append({
            "text": interpretation,
            "type": "interpretation",
            "keyword": f"{topic} analysis"
        })
    
    # 7. CHALLENGE ASSUMPTIONS
    challenge_template = random.choice(YPP_TEMPLATES["challenge"])
    challenge = challenge_template.format(
        old_belief=generate_old_belief(topic),
        topic=topic,
        new_understanding=generate_new_understanding(topic),
        conventional_wisdom=generate_old_belief(topic),
        contrary_evidence=generate_new_understanding(topic),
        old_view=generate_old_belief(topic),
        revised_view=generate_new_understanding(topic)
    )
    segments.append({"text": challenge, "type": "challenge", "keyword": f"{topic} history"})
    
    # 8. MODERN PERSPECTIVE
    modern_template = random.choice(YPP_TEMPLATES["modern_perspective"])
    modern = modern_template.format(
        topic=topic,
        modern_comparison=generate_modern_comparison(topic),
        relevance=generate_relevance(topic),
        contemporary_understanding=generate_modern_comparison(topic),
        modern_application=generate_relevance(topic),
        current_interpretation=generate_modern_comparison(topic),
        modern_significance=generate_relevance(topic)
    )
    segments.append({"text": modern, "type": "modern", "keyword": f"{topic} modern"})
    
    # 9-11. DEEPER ANALYSIS
    for i in range(3):
        analysis_template = random.choice(YPP_TEMPLATES["analysis"])
        analysis = analysis_template.format(
            reason=generate_implication(""),
            specific_aspect=f"the technical details of {topic}",
            insight=generate_interpretation(""),
            interpretation=generate_interpretation(""),
            impact=generate_broader_field(topic),
            significance=generate_implication(""),
            discovery=generate_final_insight(topic)
        )
        segments.append({
            "text": analysis,
            "type": "analysis",
            "keyword": f"{topic} details"
        })
    
    # 12. SYNTHESIS
    synthesis_template = random.choice(YPP_TEMPLATES["synthesis"])
    synthesis = synthesis_template.format(
        topic=topic,
        final_insight=generate_final_insight(topic),
        broader_field=generate_broader_field(topic),
        conclusion=generate_final_insight(topic),
        broader_context=generate_broader_field(topic),
        synthesis=generate_final_insight(topic),
        lasting_impact=generate_implication("")
    )
    segments.append({"text": synthesis, "type": "synthesis", "keyword": topic})
    
    # 13. CHANNEL IDENTITY (MANDATORY for YPP)
    identity = random.choice(YPP_TEMPLATES["identity"])
    segments.append({"text": identity, "type": "identity", "keyword": "education"})
    
    return segments

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def estimate_segment_duration(text):
    """Estimate duration in seconds (150 words per minute)"""
    words = len(text.split())
    return (words / 150) * 60

def ensure_minimum_duration(segments, min_duration=480):
    """Ensure total duration is at least min_duration seconds (8 minutes)"""
    total_duration = sum(estimate_segment_duration(seg["text"]) for seg in segments)
    
    while total_duration < min_duration:
        # Add more analytical segments
        analysis_template = random.choice(YPP_TEMPLATES["analysis"])
        topic = segments[0]["text"].split()[2] if len(segments) > 0 else "this topic"
        
        additional = analysis_template.format(
            reason=generate_implication(""),
            specific_aspect=f"another important aspect",
            insight=generate_interpretation(""),
            interpretation=generate_interpretation(""),
            impact=generate_broader_field(topic),
            significance=generate_implication(""),
            discovery=generate_final_insight(topic)
        )
        
        # Insert before synthesis and identity
        segments.insert(-2, {
            "text": additional,
            "type": "analysis",
            "keyword": f"{topic} analysis"
        })
        
        total_duration = sum(estimate_segment_duration(seg["text"]) for seg in segments)
    
    return segments
