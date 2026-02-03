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


class ConversationalSymptomAnalyzer:
    """
    Multi-step conversational symptom analyzer
    Guides user through 3-4 steps of questions to gather comprehensive information
    """

    def __init__(self):
        """Initialize conversational analyzer with OpenAI client"""
        self.use_ai = os.getenv('USE_OPENAI_AI', 'False').lower() == 'true'
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')

        if self.use_ai and self.openai_api_key:
            try:
                self.client = OpenAI(api_key=self.openai_api_key)
                print("✓ Conversational AI initialized successfully")
            except Exception as e:
                print(f"⚠ OpenAI initialization failed: {e}. Using rule-based.")
                self.use_ai = False
                self.client = None
        else:
            self.client = None

    def start_conversation(self, initial_complaint: str) -> Dict:
        """
        Start symptom conversation and generate first set of questions

        Args:
            initial_complaint: User's initial symptom description

        Returns:
            Dictionary with step info and questions
        """
        if self.use_ai and self.client:
            try:
                return self._generate_questions_ai(initial_complaint, step=1, history=[])
            except Exception as e:
                print(f"AI question generation failed: {e}. Using rule-based.")

        # Rule-based fallback
        return self._generate_questions_rule_based(initial_complaint, step=1)

    def continue_conversation(self, conversation_history: List[Dict], step: int) -> Dict:
        """
        Continue conversation with next set of questions

        Args:
            conversation_history: List of {question, answer} dicts
            step: Current step number (2 or 3)

        Returns:
            Dictionary with questions or final analysis
        """
        if step >= 4:
            # Final analysis after 3 steps of questions
            return self.finalize_analysis(conversation_history)

        if self.use_ai and self.client:
            try:
                initial_complaint = conversation_history[0]['answer'] if conversation_history else ""
                return self._generate_questions_ai(initial_complaint, step, conversation_history)
            except Exception as e:
                print(f"AI question generation failed: {e}. Using rule-based.")

        return self._generate_questions_rule_based("", step, conversation_history)

    def finalize_analysis(self, conversation_history: List[Dict]) -> Dict:
        """
        Perform final comprehensive analysis based on all conversation data

        Args:
            conversation_history: Complete conversation history

        Returns:
            Final analysis with recommendations
        """
        # Compile all information
        full_symptom_description = self._compile_symptom_description(conversation_history)

        # Use the standard analyzer for final analysis
        final_analysis = symptom_analyzer.analyze_symptoms(full_symptom_description)
        final_analysis['conversation_summary'] = conversation_history
        final_analysis['is_final'] = True

        return final_analysis

    def _generate_questions_ai(self, initial_complaint: str, step: int, history: List[Dict] = []) -> Dict:
        """Generate questions using AI based on step and conversation history"""

        if step == 1:
            # Step 1: Ask about severity, duration, location
            prompt = f"""Based on this initial symptom: "{initial_complaint}"

Generate 3 specific follow-up questions to understand:
1. The severity or intensity (scale 1-10, or description)
2. How long they've had these symptoms (duration)
3. Specific location or affected areas

Return JSON format:
{{
  "step": 1,
  "step_title": "Understanding Your Symptoms",
  "questions": [
    {{"id": "severity", "question": "...", "type": "text"}},
    {{"id": "duration", "question": "...", "type": "text"}},
    {{"id": "location", "question": "...", "type": "text"}}
  ]
}}"""

        elif step == 2:
            # Step 2: Ask about associated symptoms, triggers, patterns
            history_text = "\n".join([f"Q: {item['question']}\nA: {item['answer']}" for item in history])
            prompt = f"""Conversation so far:
{history_text}

Generate 3 follow-up questions to understand:
1. Any related or associated symptoms
2. What makes it better or worse (triggers, patterns)
3. Any recent changes in health, medications, or lifestyle

Return JSON format:
{{
  "step": 2,
  "step_title": "Additional Details",
  "questions": [
    {{"id": "related_symptoms", "question": "...", "type": "text"}},
    {{"id": "triggers", "question": "...", "type": "text"}},
    {{"id": "recent_changes", "question": "...", "type": "text"}}
  ]
}}"""

        else:  # step == 3
            # Step 3: Ask about medical history, medications, concerns
            history_text = "\n".join([f"Q: {item['question']}\nA: {item['answer']}" for item in history])
            prompt = f"""Conversation so far:
{history_text}

Generate final 3 questions to understand:
1. Relevant medical history or pre-existing conditions
2. Current medications or treatments they're taking
3. Their main concern or what worries them most

Return JSON format:
{{
  "step": 3,
  "step_title": "Medical Background",
  "questions": [
    {{"id": "medical_history", "question": "...", "type": "text"}},
    {{"id": "medications", "question": "...", "type": "text"}},
    {{"id": "main_concern", "question": "...", "type": "text"}}
  ]
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a medical AI assistant. Generate clear, empathetic questions to understand patient symptoms better."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            result['is_final'] = False
            return result

        except Exception as e:
            print(f"AI question generation error: {e}")
            raise

    def _generate_questions_rule_based(self, initial_complaint: str, step: int, history: List[Dict] = []) -> Dict:
        """Generate questions using rule-based logic (fallback)"""

        if step == 1:
            return {
                "step": 1,
                "step_title": "Understanding Your Symptoms",
                "is_final": False,
                "questions": [
                    {
                        "id": "severity",
                        "question": "On a scale of 1-10, how severe is your discomfort? (1 = mild, 10 = severe)",
                        "type": "text",
                        "placeholder": "e.g., 7 out of 10"
                    },
                    {
                        "id": "duration",
                        "question": "How long have you been experiencing these symptoms?",
                        "type": "text",
                        "placeholder": "e.g., 3 days, 2 weeks, several months"
                    },
                    {
                        "id": "location",
                        "question": "Can you describe the specific location or area affected?",
                        "type": "text",
                        "placeholder": "e.g., right side of head, lower back, entire chest"
                    }
                ]
            }

        elif step == 2:
            return {
                "step": 2,
                "step_title": "Additional Details",
                "is_final": False,
                "questions": [
                    {
                        "id": "related_symptoms",
                        "question": "Are you experiencing any other symptoms along with this? (e.g., fever, nausea, fatigue)",
                        "type": "text",
                        "placeholder": "e.g., mild fever, headache, loss of appetite"
                    },
                    {
                        "id": "triggers",
                        "question": "Does anything make it better or worse? (activities, time of day, food, etc.)",
                        "type": "text",
                        "placeholder": "e.g., worse when lying down, better after eating"
                    },
                    {
                        "id": "recent_changes",
                        "question": "Have there been any recent changes in your health, diet, or medications?",
                        "type": "text",
                        "placeholder": "e.g., started new medication, travel, stress"
                    }
                ]
            }

        else:  # step == 3
            return {
                "step": 3,
                "step_title": "Medical Background",
                "is_final": False,
                "questions": [
                    {
                        "id": "medical_history",
                        "question": "Do you have any relevant medical conditions or allergies?",
                        "type": "text",
                        "placeholder": "e.g., diabetes, high blood pressure, allergies"
                    },
                    {
                        "id": "medications",
                        "question": "What medications or supplements are you currently taking?",
                        "type": "text",
                        "placeholder": "e.g., aspirin, vitamins, prescription drugs"
                    },
                    {
                        "id": "main_concern",
                        "question": "What concerns you most about these symptoms?",
                        "type": "text",
                        "placeholder": "e.g., pain intensity, impact on work, worry about serious illness"
                    }
                ]
            }

    def _compile_symptom_description(self, conversation_history: List[Dict]) -> str:
        """Compile all conversation data into comprehensive symptom description"""
        sections = []

        for item in conversation_history:
            sections.append(f"{item['question']}: {item['answer']}")

        return " | ".join(sections)


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
conversational_analyzer = ConversationalSymptomAnalyzer()