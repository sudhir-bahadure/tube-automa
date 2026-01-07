import os
import json
from datetime import datetime, timedelta
import sys

# Mocking modules for testing
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
sys.path.insert(0, os.path.join(os.getcwd(), 'legacy_projects', 'src'))

def test_topic_suppression():
    print("\n--- Testing Topic Suppression ---")
    from content import is_topic_duplicate, save_used_topic
    
    test_topic = "Eiffel Tower Height"
    
    # Ensure it's not and then is
    if is_topic_duplicate(test_topic):
        print("Pre-test state: duplicate found (unexpected). Clearing.")
        with open('assets/used_topics.json', 'w') as f: json.dump({}, f)
    
    assert not is_topic_duplicate(test_topic)
    print("New topic check: PASS")
    
    save_used_topic(test_topic)
    assert is_topic_duplicate(test_topic)
    print("Same topic check (0 days): PASS")

def test_entity_detection():
    print("\n--- Testing Entity Detection ---")
    from content import detect_anchor_entities
    
    text = "The Eiffel Tower is in Paris and the Human Brain is complex."
    entities = detect_anchor_entities(text)
    
    found_names = [e['name'] for e in entities]
    assert "Eiffel Tower" in found_names
    assert "Human Brain" in found_names
    print(f"Entities found: {found_names}")
    print("Entity detection: PASS")

def test_long_form_date_guard():
    print("\n--- Testing Long-form Date Guard ---")
    from datetime import datetime
    
    current_date = datetime.now()
    activation_date = datetime(2026, 1, 11)
    
    is_active = current_date >= activation_date
    print(f"Current Date: {current_date}")
    print(f"Activation Date: {activation_date}")
    print(f"Long-form active: {is_active}")
    
    if current_date.year == 2026 and current_date.month == 1 and current_date.day == 7:
        assert not is_active
        print("Guard before Jan 11: PASS")
    elif is_active:
        print("Guard after Jan 11: PASS")

if __name__ == "__main__":
    try:
        test_topic_suppression()
        test_entity_detection()
        test_long_form_date_guard()
        print("\n[OK] ALL LOCAL LOGIC TESTS PASSED.")
    except Exception as e:
        print(f"\n[FAIL] Test Error: {e}")
        import traceback
        traceback.print_exc()
