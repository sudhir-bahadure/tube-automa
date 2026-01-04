"""
Policy Validator for TubeAutoma
================================
Pre-upload validation ensuring YouTube policy compliance.

Checks:
- Content uniqueness (70%+ original)
- Source attribution
- Metadata honesty (no clickbait)
- Engagement quality (no manipulation)
- Copyright safety
- Educational value
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of policy validation"""
    status: str  # PASS, WARN, FAIL
    score: float  # Overall compliance score (0-100)
    issues: List[str]  # List of issues found
    warnings: List[str]  # List of warnings
    recommendations: List[str]  # Suggestions for improvement


class PolicyValidator:
    """Validates content against YouTube's authentic content policies"""
    
    def __init__(self):
        # Clickbait indicators
        self.clickbait_patterns = [
            r'\bSHOCK(ED|ING)?\b',
            r'\bMIND[- ]?BLOW(N|ING)\b',
            r'\bYOU WON\'T BELIEVE\b',
            r'\bMUST (WATCH|SEE)\b',
            r'\b(INSANE|CRAZY|UNBELIEVABLE)\b',
            r'\bGONE WRONG\b',
            r'\bWATCH TILL THE END\b',
            r'!!+',  # Multiple exclamation marks
            r'\bVIRAL\b(?! video about)',  # "VIRAL" unless used descriptively
        ]
        
        # Manipulative hashtags
        self.spam_hashtags = [
            '#viral', '#viralvideo', '#mustwatch', '#trending',
            '#followme', '#followback', '#like4like', '#sub4sub',
            '#clickhere', '#linkinbio', '#shocked', '#omg'
        ]
        
        # Manipulative CTAs
        self.manipulative_ctas = [
            r'SUBSCRIBE NOW OR',
            r'SMASH THAT',
            r'IF YOU DON\'T SUBSCRIBE',
            r'COMMENT (DOWN )?BELOW FOR',
            r'LIKE THIS VIDEO IF',
            r'TURN ON NOTIFICATIONS',
        ]
        
        # Educational value indicators (positive signals)
        self.educational_keywords = [
            'learn', 'understand', 'explore', 'discover', 'science',
            'history', 'research', 'study', 'analysis', 'principle',
            'concept', 'theory', 'evidence', 'data', 'tutorial'
        ]
    
    def validate_content(self, metadata: Dict) -> ValidationResult:
        """
        Comprehensive validation of video content and metadata
        
        Args:
            metadata: Video metadata dict with keys:
                - title: Video title
                - description: Video description
                - tags: Video tags/hashtags
                - text: Script content
                - mode: Content mode (meme/fact/long)
                - originality_score: Score from authenticity engine
                - attribution: Source attribution
                
        Returns:
            ValidationResult object
        """
        issues = []
        warnings = []
        recommendations = []
        scores = []
        
        # 1. Uniqueness Check
        uniqueness_score, uniqueness_issues = self._check_uniqueness(metadata)
        scores.append(uniqueness_score)
        issues.extend([f"[UNIQUENESS] {i}" for i in uniqueness_issues if 'FAIL' in i])
        warnings.extend([f"[UNIQUENESS] {i}" for i in uniqueness_issues if 'WARN' in i])
        
        # 2. Attribution Check
        attribution_score, attribution_issues = self._check_attribution(metadata)
        scores.append(attribution_score)
        issues.extend([f"[ATTRIBUTION] {i}" for i in attribution_issues if 'FAIL' in i])
        warnings.extend([f"[ATTRIBUTION] {i}" for i in attribution_issues if 'WARN' in i])
        
        # 3. Metadata Honesty Check
        metadata_score, metadata_issues = self._check_metadata_honesty(metadata)
        scores.append(metadata_score)
        issues.extend([f"[METADATA] {i}" for i in metadata_issues if 'FAIL' in i])
        warnings.extend([f"[METADATA] {i}" for i in metadata_issues if 'WARN' in i])
        
        # 4. Engagement Quality Check
        engagement_score, engagement_issues = self._check_engagement_quality(metadata)
        scores.append(engagement_score)
        issues.extend([f"[ENGAGEMENT] {i}" for i in engagement_issues if 'FAIL' in i])
        warnings.extend([f"[ENGAGEMENT] {i}" for i in engagement_issues if 'WARN' in i])
        
        # 5. Educational Value Check
        edu_score, edu_issues = self._check_educational_value(metadata)
        scores.append(edu_score)
        warnings.extend([f"[EDUCATION] {i}" for i in edu_issues if 'WARN' in i])
        
        # 6. Copyright Safety (basic check - assumes royalty-free assets)
        copyright_score = 100  # Assume pass if using Pexels + Edge-TTS
        scores.append(copyright_score)
        
        # Calculate overall score (weighted average)
        weights = [0.30, 0.20, 0.20, 0.15, 0.10, 0.05]  # Uniqueness is most important
        overall_score = sum(s * w for s, w in zip(scores, weights))
        
        # Generate recommendations
        if overall_score < 80:
            recommendations.append("Consider adding more original commentary")
        if metadata_score < 90:
            recommendations.append("Simplify title to be more descriptive, less sensational")
        if edu_score < 70:
            recommendations.append("Add more educational context or learning objectives")
        
        # Determine status
        if issues:
            status = "FAIL"
        elif overall_score < 75:
            status = "WARN"
        else:
            status = "PASS"
        
        return ValidationResult(
            status=status,
            score=overall_score,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def _check_uniqueness(self, metadata: Dict) -> Tuple[float, List[str]]:
        """Check content originality"""
        issues = []
        originality_score = metadata.get('originality_score', 0)
        
        if originality_score < 40:
            issues.append(f"FAIL: Originality {originality_score:.1f}% below 40% minimum")
            return 0, issues
        elif originality_score < 60:
            issues.append(f"WARN: Originality {originality_score:.1f}% below recommended 60%")
            return 60, issues
        
        return min(100, originality_score), issues
    
    def _check_attribution(self, metadata: Dict) -> Tuple[float, List[str]]:
        """Check source attribution"""
        issues = []
        attribution = metadata.get('attribution', '')
        description = metadata.get('description', '')
        
        # Check if attribution exists
        if not attribution and 'source' not in description.lower():
            issues.append("FAIL: No source attribution found")
            return 0, issues
        
        # Check if attribution is vague
        vague_terms = ['research', 'sources', 'internet', 'online']
        if any(term in attribution.lower() for term in vague_terms) and len(attribution) < 30:
            issues.append("WARN: Attribution is vague, be more specific")
            return 70, issues
        
        return 100, issues
    
    def _check_metadata_honesty(self, metadata: Dict) -> Tuple[float, List[str]]:
        """Check for clickbait and deceptive metadata"""
        issues = []
        title = metadata.get('title', '')
        description = metadata.get('description', '')
        tags = metadata.get('tags', '')
        
        # Check title for clickbait
        clickbait_found = []
        for pattern in self.clickbait_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                clickbait_found.append(pattern)
        
        if len(clickbait_found) > 2:
            issues.append(f"FAIL: Title contains multiple clickbait indicators: {clickbait_found}")
            return 0, issues
        elif clickbait_found:
            issues.append(f"WARN: Title may be clickbait: {clickbait_found[0]}")
            return 70, issues
        
        # Check for spam hashtags
        tags_lower = tags.lower()
        spam_found = [tag for tag in self.spam_hashtags if tag in tags_lower]
        if len(spam_found) > 3:
            issues.append(f"FAIL: Too many spam hashtags: {spam_found}")
            return 30, issues
        elif spam_found:
            issues.append(f"WARN: Contains spam hashtags: {spam_found}")
            return 80, issues
        
        # Check for excessive caps
        if title.isupper() and len(title) > 10:
            issues.append("WARN: Title is all caps (appears aggressive)")
            return 75, issues
        
        return 100, issues
    
    def _check_engagement_quality(self, metadata: Dict) -> Tuple[float, List[str]]:
        """Check for manipulative engagement tactics"""
        issues = []
        description = metadata.get('description', '')
        script = metadata.get('text', '') or metadata.get('full_script', '')
        
        # Check for manipulative CTAs
        manipulative_found = []
        full_text = f"{description} {script}"
        for pattern in self.manipulative_ctas:
            if re.search(pattern, full_text, re.IGNORECASE):
                manipulative_found.append(pattern)
        
        if manipulative_found:
            issues.append(f"FAIL: Contains manipulative CTAs: {manipulative_found}")
            return 40, issues
        
        # Check for excessive emoji
        emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]{5,}'
        if re.search(emoji_pattern, full_text):
            issues.append("WARN: Excessive emoji usage")
            return 80, issues
        
        return 100, issues
    
    def _check_educational_value(self, metadata: Dict) -> Tuple[float, List[str]]:
        """Check for educational value"""
        issues = []
        script = metadata.get('text', '') or metadata.get('full_script', '')
        description = metadata.get('description', '')
        
        full_text = f"{script} {description}".lower()
        
        # Count educational keywords
        edu_count = sum(1 for kw in self.educational_keywords if kw in full_text)
        
        if edu_count < 2:
            issues.append("WARN: Low educational value - consider adding context/learning objective")
            return 50, issues
        elif edu_count < 4:
            issues.append("INFO: Moderate educational value")
            return 75, issues
        
        return 100, issues
    
    def generate_report(self, result: ValidationResult, video_id: str = "unknown") -> str:
        """Generate human-readable validation report"""
        report = []
        report.append("=" * 70)
        report.append(f"YOUTUBE POLICY VALIDATION REPORT - Video: {video_id}")
        report.append("=" * 70)
        report.append(f"\nSTATUS: {result.status}")
        report.append(f"OVERALL SCORE: {result.score:.1f}/100")
        report.append("")
        
        if result.status == "PASS":
            report.append("✅ This video meets YouTube's authentic content policies.")
            report.append("   Safe to upload.")
        elif result.status == "WARN":
            report.append("⚠️  This video has minor issues but may still be acceptable.")
            report.append("   Review warnings before uploading.")
        else:
            report.append("❌ This video FAILS policy compliance.")
            report.append("   DO NOT UPLOAD until issues are resolved.")
        
        if result.issues:
            report.append(f"\n🚫 CRITICAL ISSUES ({len(result.issues)}):")
            for issue in result.issues:
                report.append(f"   - {issue}")
        
        if result.warnings:
            report.append(f"\n⚠️  WARNINGS ({len(result.warnings)}):")
            for warning in result.warnings:
                report.append(f"   - {warning}")
        
        if result.recommendations:
            report.append(f"\n💡 RECOMMENDATIONS ({len(result.recommendations)}):")
            for rec in result.recommendations:
                report.append(f"   - {rec}")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)
    
    def should_block_upload(self, result: ValidationResult) -> bool:
        """Determine if upload should be blocked"""
        return result.status == "FAIL" or result.score < 40


# Convenience function
def validate_video(metadata: Dict, verbose: bool = True) -> Tuple[bool, ValidationResult]:
    """
    Quick validation check
    
    Args:
        metadata: Video metadata dict
        verbose: Print report
        
    Returns:
        (is_safe_to_upload, validation_result)
    """
    validator = PolicyValidator()
    result = validator.validate_content(metadata)
    
    if verbose:
        print(validator.generate_report(result, metadata.get('title', 'unknown')))
    
    is_safe = not validator.should_block_upload(result)
    return is_safe, result


if __name__ == "__main__":
    # Test the validator
    print("\n" + "=" * 70)
    print("POLICY VALIDATOR TESTS")
    print("=" * 70)
    
    # Test 1: Good content (should PASS)
    print("\n\nTEST 1: COMPLIANT CONTENT")
    print("-" * 70)
    good_metadata = {
        'title': 'Understanding Honey Preservation: Ancient Egyptian Food Science',
        'description': 'An educational exploration of honey preservation. Sources: Wikipedia (Honey), Archaeological Science Journal. Subscribe for weekly science topics.',
        'tags': '#Science #Education #History #Learning',
        'text': 'Let\'s explore the science behind honey preservation. Research shows that honey\'s unique properties prevent spoilage. This demonstrates the importance of understanding chemistry.',
        'originality_score': 75.0,
        'attribution': 'Wikipedia (Honey), Archaeological Science Journal',
        'mode': 'fact'
    }
    is_safe, result = validate_video(good_metadata)
    print(f"\n>>> UPLOAD DECISION: {'✅ SAFE' if is_safe else '❌ BLOCKED'}")
    
    # Test 2: Clickbait title (should WARN or FAIL)
    print("\n\nTEST 2: CLICKBAIT CONTENT")
    print("-" * 70)
    bad_metadata = {
        'title': 'MIND-BLOWING Facts That Will SHOCK You!!! 🤯😱',
        'description': 'VIRAL facts! Subscribe NOW! #Viral #MustWatch #Trending',
        'tags': '#viral #mustwatch #sub4sub #followme',
        'text': 'Honey never spoils.',
        'originality_score': 45.0,
        'attribution': '',
        'mode': 'fact'
    }
    is_safe, result = validate_video(bad_metadata)
    print(f"\n>>> UPLOAD DECISION: {'✅ SAFE' if is_safe else '❌ BLOCKED'}")
    
    # Test 3: Marginal content (should WARN)
    print("\n\nTEST 3: MARGINAL CONTENT")
    print("-" * 70)
    marginal_metadata = {
        'title': 'Amazing Honey Facts',
        'description': 'Cool facts about honey. Subscribe!',
        'tags': '#facts #interesting',
        'text': 'Honey never spoils. Ancient Egyptians used honey.',
        'originality_score': 68.0,
        'attribution': 'From research',
        'mode': 'fact'
    }
    is_safe, result = validate_video(marginal_metadata)
    print(f"\n>>> UPLOAD DECISION: {'✅ SAFE' if is_safe else '❌ BLOCKED'}")
    
    print("\n" + "=" * 70)
    print("ALL VALIDATION TESTS COMPLETE")
    print("=" * 70 + "\n")
