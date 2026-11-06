import unittest
from src.quality_gate import validate_script_data

class ScriptQualityTests(unittest.TestCase):
    def test_accepts_distinct_short_script(self):
        scenes = []
        for i in range(8):
            scenes.append({
                'text': 'This scene explains a different everyday example and useful psychological insight number ' + str(i) + ' clearly.',
                'visual_prompt': 'Stickman illustration with unique prop and pose number ' + str(i) + ' in a room.'
            })
        result = validate_script_data({'title': 'Why silence feels uncomfortable', 'scenes': scenes}, is_short=True)
        self.assertEqual(result['scenes'], 8)

    def test_rejects_repeated_narration(self):
        scenes = [
            {'text': 'This exact narration repeats in every single scene.', 'visual_prompt': 'Unique visual composition number ' + str(i) + ' with an object.'}
            for i in range(8)
        ]
        with self.assertRaisesRegex(ValueError, 'repeats'):
            validate_script_data({'title': 'Repeated scene test', 'scenes': scenes}, is_short=True)

if __name__ == '__main__':
    unittest.main()
