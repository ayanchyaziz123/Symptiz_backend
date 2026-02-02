#!/usr/bin/env python
"""
Test script for AI Symptom Checker
Tests both rule-based and OpenAI-powered analysis
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from symptoms.ai_service import symptom_analyzer, doctor_recommender
import json


def print_analysis(result, title="Analysis Result"):
    """Pretty print analysis result"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)
    print(f"Urgency Level: {result['urgency_level'].upper()}")
    print(f"Confidence: {result['confidence_score']:.2f}")
    print(f"\nRecommendation:")
    print(f"  {result['recommendation']}")
    print(f"\nProvider Type: {result['recommended_provider_type']}")
    print(f"\nPossible Conditions:")
    conditions = json.loads(result['possible_conditions'])
    for condition in conditions:
        print(f"  - {condition}")

    # Print AI metadata if available
    if result.get('ai_metadata'):
        metadata = json.loads(result['ai_metadata'])
        print(f"\nModel Used: {metadata.get('model_used', 'N/A')}")

        if metadata.get('red_flags'):
            print(f"\nRed Flags:")
            for flag in metadata['red_flags']:
                print(f"  ⚠️  {flag}")

        if metadata.get('self_care_tips'):
            print(f"\nSelf-Care Tips:")
            for tip in metadata['self_care_tips']:
                print(f"  💡 {tip}")

    print('=' * 60)


def test_symptom_analysis():
    """Test various symptom scenarios"""

    print("\n" + "=" * 60)
    print("  AI SYMPTOM CHECKER TEST")
    print("=" * 60)

    # Check AI configuration
    print(f"\nAI Configuration:")
    print(f"  USE_OPENAI_AI: {os.getenv('USE_OPENAI_AI', 'False')}")
    print(f"  API Key Set: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
    print(f"  Using AI: {symptom_analyzer.use_ai}")
    print(f"  Client Initialized: {symptom_analyzer.client is not None}")

    # Test cases
    test_cases = [
        {
            "name": "Emergency Case",
            "symptoms": "I have severe chest pain that radiates to my left arm, difficulty breathing, and I'm sweating profusely"
        },
        {
            "name": "Urgent Care Case",
            "symptoms": "I have a high fever of 103°F for the past 2 days, severe cough, and body aches"
        },
        {
            "name": "Doctor Visit Case",
            "symptoms": "I've been having persistent headaches for the past week, along with some dizziness"
        },
        {
            "name": "Mild/Home Care Case",
            "symptoms": "I have a mild runny nose and a slightly scratchy throat, feeling a bit tired"
        },
        {
            "name": "Specialty-Specific Case",
            "symptoms": "I have a painful rash on my arms that's been spreading, it's red and itchy"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        try:
            print(f"\n\n{'*' * 60}")
            print(f"  TEST CASE {i}: {test_case['name']}")
            print('*' * 60)
            print(f"\nSymptoms: {test_case['symptoms']}")

            # Run analysis
            result = symptom_analyzer.analyze_symptoms(test_case['symptoms'])

            # Print results
            print_analysis(result, f"Analysis for {test_case['name']}")

            # Get recommended specialties
            specialties = doctor_recommender.get_recommended_specialties(
                test_case['symptoms'],
                result['urgency_level']
            )

            if specialties:
                print(f"\nRecommended Specialties:")
                for specialty in specialties:
                    print(f"  🏥 {specialty}")

        except Exception as e:
            print(f"\n❌ ERROR in {test_case['name']}:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("  TEST COMPLETED")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    test_symptom_analysis()
