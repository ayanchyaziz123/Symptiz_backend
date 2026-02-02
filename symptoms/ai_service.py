"""
AI Service for Symptom Analysis
Hybrid approach: OpenAI GPT for accuracy + Rule-based fallback
"""
import json
import os
from typing import Dict, List
from openai import OpenAI


class SymptomAnalyzerAI:
    """
    Hybrid symptom analyzer
    Uses OpenAI GPT-4 for accurate analysis with rule-based fallback
    """

    def __init__(self):
        """Initialize AI service with OpenAI client"""
        self.use_ai = os.getenv('USE_OPENAI_AI', 'False').lower() == 'true'
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')

        if self.use_ai and self.openai_api_key:
            try:
                self.client = OpenAI(api_key=self.openai_api_key)
                print("✓ OpenAI AI initialized successfully")
            except Exception as e:
                print(f"⚠ OpenAI initialization failed: {e}. Falling back to rule-based.")
                self.use_ai = False
                self.client = None
        else:
            self.client = None
            if not self.openai_api_key:
                print("ℹ No OpenAI API key found. Using rule-based analysis.")

    def analyze_symptoms(self, symptoms_description: str) -> Dict:
        """
        Analyze patient symptoms and return recommendations
        Uses OpenAI GPT if available, otherwise falls back to rule-based

        Args:
            symptoms_description: Patient's description of symptoms

        Returns:
            Dictionary with analysis results
        """
        # Try OpenAI analysis first
        if self.use_ai and self.client:
            try:
                return self._analyze_with_openai(symptoms_description)
            except Exception as e:
                print(f"OpenAI analysis failed: {e}. Using rule-based fallback.")
                # Fall through to rule-based analysis

        # Rule-based analysis (fallback)
        return self._analyze_rule_based(symptoms_description)

    def _analyze_with_openai(self, symptoms_description: str) -> Dict:
        """
        Analyze symptoms using OpenAI GPT-4

        Args:
            symptoms_description: Patient's description of symptoms

        Returns:
            Dictionary with AI analysis results
        """
        system_prompt = """You are a medical triage AI assistant. Analyze patient symptoms and provide:
1. Urgency level (emergency/urgent_care/doctor_visit/home_care)
2. Brief recommendation
3. Recommended provider type
4. Possible conditions (3-5 most likely)
5. Confidence score (0.0-1.0)
6. Self-care tips if applicable

CRITICAL SAFETY RULES:
- If symptoms suggest emergency (chest pain, difficulty breathing, severe bleeding, stroke signs, loss of consciousness), ALWAYS classify as 'emergency'
- Err on the side of caution - when in doubt, escalate urgency level
- Never diagnose - only suggest possibilities
- Always recommend professional medical evaluation for concerning symptoms

Respond in JSON format:
{
  "urgency_level": "emergency|urgent_care|doctor_visit|home_care",
  "recommendation": "specific recommendation text",
  "recommended_provider_type": "Emergency Room|Urgent Care|Specialist Name|Primary Care|Self-care",
  "possible_conditions": ["condition1", "condition2", "condition3"],
  "confidence_score": 0.85,
  "self_care_tips": ["tip1", "tip2"],
  "red_flags": ["flag1", "flag2"]
}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini for cost-effectiveness
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Patient symptoms: {symptoms_description}"}
                ],
                temperature=0.3,  # Lower temperature for more consistent medical advice
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            ai_response = json.loads(response.choices[0].message.content)

            # Format response to match database schema
            return {
                'symptoms_description': symptoms_description,
                'urgency_level': ai_response.get('urgency_level', 'doctor_visit'),
                'recommendation': ai_response.get('recommendation', ''),
                'recommended_provider_type': ai_response.get('recommended_provider_type', 'Primary Care Physician'),
                'confidence_score': float(ai_response.get('confidence_score', 0.85)),
                'possible_conditions': json.dumps(ai_response.get('possible_conditions', [])),
                'follow_up_needed': ai_response.get('urgency_level') != 'home_care',
                'ai_metadata': json.dumps({
                    'red_flags': ai_response.get('red_flags', []),
                    'self_care_tips': ai_response.get('self_care_tips', []),
                    'model_used': 'gpt-4o-mini',
                    'raw_response': ai_response
                })
            }

        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            raise

    def _analyze_rule_based(self, symptoms_description: str) -> Dict:
        """
        Rule-based symptom analysis (fallback method)

        Args:
            symptoms_description: Patient's description of symptoms

        Returns:
            Dictionary with analysis results
        """
        try:
            symptoms_lower = symptoms_description.lower()
            
            # Emergency keywords
            emergency_keywords = {
                'chest pain', 'chest pressure', 'can\'t breathe', 'difficulty breathing', 
                'shortness of breath', 'severe bleeding', 'unconscious', 'unresponsive',
                'stroke', 'heart attack', 'severe pain', 'suicide', 'suicidal',
                'overdose', 'seizure', 'severe burn', 'paralysis', 'sudden weakness',
                'severe headache', 'sudden confusion', 'loss of consciousness',
                'coughing blood', 'vomiting blood', 'severe allergic reaction'
            }
            
            # Urgent care keywords
            urgent_keywords = {
                'high fever', 'persistent fever', 'severe vomiting', 'severe diarrhea',
                'dehydration', 'difficulty urinating', 'blood in urine', 'severe cough',
                'broken bone', 'sprained ankle', 'deep cut', 'animal bite',
                'severe rash', 'eye injury', 'ear infection'
            }
            
            # Doctor visit keywords by specialty
            specialty_keywords = {
                'cardiology': ['heart', 'palpitations', 'irregular heartbeat', 'chest discomfort'],
                'dermatology': ['skin', 'rash', 'acne', 'mole', 'eczema', 'psoriasis', 'hives'],
                'orthopedics': ['bone', 'joint', 'fracture', 'sprain', 'back pain', 'knee pain'],
                'gastroenterology': ['stomach', 'digestion', 'nausea', 'diarrhea', 'constipation', 'abdominal'],
                'neurology': ['headache', 'migraine', 'dizziness', 'numbness', 'tingling'],
                'respiratory': ['cough', 'breathing', 'lungs', 'asthma', 'bronchitis'],
                'ent': ['ear', 'nose', 'throat', 'sinus', 'tonsil'],
                'ophthalmology': ['eye', 'vision', 'blurry', 'blind', 'double vision'],
                'mental_health': ['anxiety', 'depression', 'stress', 'mental', 'panic', 'worried'],
                'pediatrics': ['child', 'baby', 'infant', 'toddler'],
                'urology': ['urinary', 'bladder', 'kidney', 'urination'],
                'gynecology': ['menstrual', 'period', 'pregnancy', 'vaginal', 'pelvic'],
            }
            
            # Check for emergency
            if any(keyword in symptoms_lower for keyword in emergency_keywords):
                return {
                    'symptoms_description': symptoms_description,
                    'urgency_level': 'emergency',
                    'recommendation': 'SEEK IMMEDIATE EMERGENCY CARE. Call 911 or go to the nearest emergency room immediately. Do not drive yourself.',
                    'recommended_provider_type': 'Emergency Room',
                    'confidence_score': 0.95,
                    'possible_conditions': json.dumps(['Medical Emergency - Immediate Evaluation Required']),
                    'follow_up_needed': True,
                    'ai_metadata': json.dumps({
                        'red_flags': ['Emergency symptoms detected'],
                        'self_care_tips': [],
                        'model_used': 'rule_based'
                    })
                }
            
            # Check for urgent care
            elif any(keyword in symptoms_lower for keyword in urgent_keywords):
                return {
                    'symptoms_description': symptoms_description,
                    'urgency_level': 'urgent_care',
                    'recommendation': 'Visit an urgent care clinic or emergency room within the next few hours. Your symptoms require prompt medical attention.',
                    'recommended_provider_type': 'Urgent Care',
                    'confidence_score': 0.85,
                    'possible_conditions': json.dumps(['Requires Urgent Medical Evaluation']),
                    'follow_up_needed': True,
                    'ai_metadata': json.dumps({
                        'red_flags': ['Urgent symptoms detected'],
                        'self_care_tips': [],
                        'model_used': 'rule_based'
                    })
                }
            
            # Check for specialty-specific symptoms
            detected_specialty = None
            specialty_name = 'Primary Care Physician'
            possible_conditions = []
            
            for specialty, keywords in specialty_keywords.items():
                if any(keyword in symptoms_lower for keyword in keywords):
                    detected_specialty = specialty
                    specialty_name = self._get_specialty_name(specialty)
                    possible_conditions = self._get_conditions_for_specialty(specialty, symptoms_lower)
                    break
            
            # Check if symptoms are mild
            mild_keywords = {
                'mild', 'slight', 'minor', 'little', 'runny nose', 'stuffy nose',
                'scratchy throat', 'tired', 'fatigue', 'common cold'
            }
            
            is_mild = any(keyword in symptoms_lower for keyword in mild_keywords)
            
            if is_mild:
                return {
                    'symptoms_description': symptoms_description,
                    'urgency_level': 'home_care',
                    'recommendation': 'Rest, stay hydrated, and monitor your symptoms. Over-the-counter medications may help relieve symptoms. Seek medical attention if symptoms worsen or persist for more than 7 days.',
                    'recommended_provider_type': 'Self-care',
                    'confidence_score': 0.75,
                    'possible_conditions': json.dumps(['Mild Symptoms - Self-care Appropriate', 'Common Cold', 'Minor Viral Infection']),
                    'follow_up_needed': False,
                    'ai_metadata': json.dumps({
                        'red_flags': [],
                        'self_care_tips': [
                            'Get plenty of rest',
                            'Stay well hydrated',
                            'Use over-the-counter medications as directed',
                            'Monitor your temperature',
                            'Seek care if symptoms worsen'
                        ],
                        'model_used': 'rule_based'
                    })
                }
            
            # Default to doctor visit
            return {
                'symptoms_description': symptoms_description,
                'urgency_level': 'doctor_visit',
                'recommendation': f'Schedule an appointment with a {specialty_name} within the next few days. Your symptoms should be evaluated by a healthcare professional.',
                'recommended_provider_type': specialty_name,
                'confidence_score': 0.80,
                'possible_conditions': json.dumps(possible_conditions if possible_conditions else ['Requires Medical Evaluation']),
                'follow_up_needed': True,
                'ai_metadata': json.dumps({
                    'red_flags': [],
                    'self_care_tips': [
                        'Monitor your symptoms',
                        'Keep a symptom diary',
                        'Note any changes or worsening',
                        'Prepare questions for your doctor'
                    ],
                    'model_used': 'rule_based'
                })
            }
            
        except Exception as e:
            print(f"Analysis Error: {str(e)}")
            # Fallback response
            return {
                'symptoms_description': symptoms_description,
                'urgency_level': 'doctor_visit',
                'recommendation': 'Please consult a healthcare provider for proper evaluation of your symptoms.',
                'recommended_provider_type': 'Primary Care Physician',
                'confidence_score': 0.60,
                'possible_conditions': json.dumps(['Requires Medical Evaluation']),
                'follow_up_needed': True,
                'ai_metadata': json.dumps({
                    'red_flags': [],
                    'self_care_tips': [],
                    'model_used': 'rule_based_fallback'
                })
            }
    
    def _get_specialty_name(self, specialty_key: str) -> str:
        """Convert specialty key to proper name"""
        specialty_names = {
            'cardiology': 'Cardiologist',
            'dermatology': 'Dermatologist',
            'orthopedics': 'Orthopedic Specialist',
            'gastroenterology': 'Gastroenterologist',
            'neurology': 'Neurologist',
            'respiratory': 'Pulmonologist',
            'ent': 'ENT Specialist',
            'ophthalmology': 'Ophthalmologist',
            'mental_health': 'Mental Health Professional',
            'pediatrics': 'Pediatrician',
            'urology': 'Urologist',
            'gynecology': 'Gynecologist',
        }
        return specialty_names.get(specialty_key, 'Primary Care Physician')
    
    def _get_conditions_for_specialty(self, specialty: str, symptoms: str) -> List[str]:
        """Get possible conditions based on specialty and symptoms"""
        conditions_map = {
            'cardiology': ['Cardiac concerns', 'Heart rhythm issues', 'Hypertension'],
            'dermatology': ['Skin condition', 'Allergic reaction', 'Dermatitis', 'Infection'],
            'orthopedics': ['Musculoskeletal injury', 'Arthritis', 'Strain or sprain'],
            'gastroenterology': ['Digestive disorder', 'Gastritis', 'IBS', 'Food intolerance'],
            'neurology': ['Neurological condition', 'Migraine', 'Tension headache'],
            'respiratory': ['Respiratory infection', 'Bronchitis', 'Asthma exacerbation'],
            'ent': ['Ear infection', 'Sinusitis', 'Tonsillitis', 'Upper respiratory infection'],
            'ophthalmology': ['Eye condition', 'Vision problem', 'Conjunctivitis'],
            'mental_health': ['Anxiety disorder', 'Depression', 'Stress-related condition'],
            'pediatrics': ['Childhood illness', 'Viral infection', 'Developmental concern'],
            'urology': ['Urinary tract infection', 'Kidney condition', 'Bladder issue'],
            'gynecology': ['Gynecological condition', 'Menstrual disorder', 'Reproductive health issue'],
        }
        return conditions_map.get(specialty, ['Requires Medical Evaluation'])


class DoctorRecommendationAI:
    """
    Service to recommend doctors and specialties based on symptoms
    """
    
    def get_recommended_specialties(self, symptoms: str, urgency_level: str) -> List[str]:
        """
        Get recommended medical specialties based on symptoms
        
        Args:
            symptoms: Patient symptoms
            urgency_level: Determined urgency level
            
        Returns:
            List of recommended medical specialties
        """
        if urgency_level == 'emergency':
            return ['Emergency Medicine']
        
        if urgency_level == 'home_care':
            return []
        
        symptoms_lower = symptoms.lower()
        
        specialty_keywords = {
            'Dermatology': ['skin', 'rash', 'acne', 'mole', 'eczema', 'psoriasis'],
            'Cardiology': ['heart', 'chest', 'palpitations', 'irregular heartbeat'],
            'Orthopedics': ['bone', 'joint', 'fracture', 'sprain', 'back pain', 'knee'],
            'Gastroenterology': ['stomach', 'digestion', 'nausea', 'diarrhea', 'abdominal'],
            'Neurology': ['headache', 'migraine', 'dizziness', 'numbness', 'tingling'],
            'Pulmonology': ['lung', 'breathing', 'cough', 'asthma', 'bronchitis'],
            'ENT': ['ear', 'nose', 'throat', 'sinus', 'tonsil'],
            'Ophthalmology': ['eye', 'vision', 'blurry', 'sight'],
            'Psychiatry': ['anxiety', 'depression', 'stress', 'mental', 'panic'],
            'Pediatrics': ['child', 'baby', 'infant', 'toddler'],
            'Urology': ['urinary', 'bladder', 'kidney'],
            'Gynecology': ['menstrual', 'period', 'pregnancy', 'vaginal'],
            'Internal Medicine': ['fever', 'infection', 'general illness'],
        }
        
        recommended = []
        for specialty, keywords in specialty_keywords.items():
            if any(keyword in symptoms_lower for keyword in keywords):
                recommended.append(specialty)
        
        # Default to Family Medicine and Internal Medicine if no specialty matches
        if not recommended:
            recommended = ['Family Medicine', 'Internal Medicine']
        
        return recommended[:3]  # Return max 3 specialties


# Singleton instances
symptom_analyzer = SymptomAnalyzerAI()
doctor_recommender = DoctorRecommendationAI()