# AI Symptom Checker Documentation

## Overview

The AI Symptom Checker uses a **hybrid approach** to provide accurate medical triage recommendations:

1. **OpenAI GPT-4o-mini** (Primary): Advanced AI analysis using OpenAI's language model
2. **Rule-based System** (Fallback): Keyword-based analysis when AI is unavailable

## Features

- **Urgency Classification**: Emergency, Urgent Care, Doctor Visit, or Home Care
- **Smart Recommendations**: Specific provider types and specialties
- **Possible Conditions**: 3-5 most likely conditions
- **Confidence Scoring**: 0.0-1.0 confidence level
- **Safety-First**: Always errs on the side of caution
- **Self-Care Tips**: For non-emergency cases
- **Red Flags**: Highlights concerning symptoms

## Configuration

### Environment Variables

Add these to your `.env` file (or copy from `.env.example`):

```bash
# Enable/Disable OpenAI AI (default: false)
USE_OPENAI_AI=true

# OpenAI API Key (get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-your-api-key-here

# Optional: Model selection (default: gpt-4o-mini)
# OPENAI_MODEL=gpt-4o-mini
```

### Getting an OpenAI API Key

1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key and add it to your `.env` file

**Note**: OpenAI API has usage costs. `gpt-4o-mini` is the most cost-effective option (~$0.15 per 1M input tokens).

## API Endpoints

### Quick Analysis (No Database Save)

**Endpoint**: `POST /api/symptoms/checks/analyze/`

**Request**:
```json
{
  "symptoms": "I have a severe headache and fever"
}
```

**Response**:
```json
{
  "urgency": "doctor_visit",
  "recommendation": "Schedule an appointment with a Neurologist...",
  "provider_type": "Neurologist",
  "confidence": 0.85,
  "possible_conditions": ["Neurological condition", "Migraine", "Tension headache"],
  "recommended_specialties": ["Neurology"],
  "follow_up_needed": true
}
```

### Create Symptom Check (Saves to Database)

**Endpoint**: `POST /api/symptoms/checks/`

**Request**:
```json
{
  "symptoms_description": "I have a severe headache and fever"
}
```

**Response**: Full SymptomCheck object with AI analysis

## Urgency Levels

### Emergency
- Immediate ER visit required
- Examples: Chest pain, difficulty breathing, severe bleeding, stroke signs
- **Action**: Call 911 or go to ER immediately

### Urgent Care
- Medical attention needed within hours
- Examples: High fever, severe vomiting, broken bones, deep cuts
- **Action**: Visit urgent care or ER today

### Doctor Visit
- Schedule appointment within days
- Examples: Persistent headaches, skin rashes, joint pain
- **Action**: Book appointment with appropriate specialist

### Home Care
- Self-care appropriate
- Examples: Mild cold, minor fatigue, slight congestion
- **Action**: Rest, hydrate, monitor symptoms

## How It Works

### With OpenAI (USE_OPENAI_AI=true)

1. Sends symptoms to GPT-4o-mini with medical triage system prompt
2. AI analyzes symptoms considering:
   - Emergency indicators
   - Symptom severity and duration
   - Possible conditions
   - Appropriate care level
3. Returns structured JSON response
4. Falls back to rule-based if API call fails

### Without OpenAI (USE_OPENAI_AI=false)

1. Uses keyword matching against curated medical dictionaries
2. Emergency keywords: chest pain, difficulty breathing, etc.
3. Urgent keywords: high fever, severe vomiting, etc.
4. Specialty keywords: categorizes by medical specialty
5. Mild symptom detection for home care

## Testing

Run the test script to verify functionality:

```bash
cd backend
source ../venv/bin/activate
python test_ai_service.py
```

This tests 5 scenarios:
- Emergency case
- Urgent care case
- Doctor visit case
- Home care case
- Specialty-specific case

## Safety Considerations

**IMPORTANT MEDICAL DISCLAIMERS**:

1. This is a **triage tool**, not a diagnostic tool
2. Always recommends professional evaluation for concerning symptoms
3. Errs on the side of caution - escalates when uncertain
4. Emergency symptoms ALWAYS result in emergency classification
5. Not a substitute for professional medical advice

## Performance

### OpenAI Mode
- **Response Time**: 1-3 seconds
- **Cost**: ~$0.0001 per analysis (using gpt-4o-mini)
- **Accuracy**: High (uses medical knowledge from training)

### Rule-Based Mode
- **Response Time**: <100ms
- **Cost**: Free
- **Accuracy**: Good for common symptoms

## Future Enhancements

The current implementation is a **small model** foundation. Future plans:

1. **Fine-tuned Medical Model**: Train custom model on medical data
2. **Symptom History Integration**: Consider user's medical history
3. **Multi-symptom Analysis**: Better handling of complex symptom combinations
4. **Location-based Recommendations**: Suggest nearby healthcare providers
5. **Follow-up Tracking**: Monitor symptom progression over time
6. **Multilingual Support**: Support for multiple languages
7. **Image Analysis**: Analyze photos of rashes, injuries, etc.
8. **Vital Signs Integration**: Include temperature, blood pressure, etc.

## Troubleshooting

### "No OpenAI API key found"
- Set `OPENAI_API_KEY` in your `.env` file
- System will automatically use rule-based analysis

### "OpenAI initialization failed"
- Check API key is valid
- Verify internet connection
- Check OpenAI API status: [status.openai.com](https://status.openai.com)

### Low confidence scores
- Provide more detailed symptom descriptions
- Include duration, severity, and context
- Mention any related symptoms

## Code Structure

```
symptoms/
├── ai_service.py           # Main AI logic
│   ├── SymptomAnalyzerAI   # Hybrid analysis engine
│   └── DoctorRecommendationAI  # Specialty recommendations
├── views.py                # API endpoints
├── models.py               # Database models
├── serializers.py          # API serialization
└── AI_README.md           # This file
```

## Contributing

When enhancing the AI system:

1. Maintain backward compatibility with rule-based system
2. Always include fallback mechanisms
3. Test with diverse symptom descriptions
4. Follow medical safety guidelines
5. Update tests when adding new features

## License & Disclaimer

This software is provided for educational and triage purposes only. It is not intended to diagnose, treat, cure, or prevent any disease. Always seek the advice of a qualified healthcare provider with any questions you may have regarding a medical condition.
