#!/usr/bin/env python3
"""
Questionnaire Response Processor
Processes and exports questionnaire responses for analysis.
"""

import json
import csv
import os
from datetime import datetime

def load_questionnaire_responses(session_data):
    """Load responses from session data"""
    return session_data.get('questionnaire_responses', {})

def export_responses_to_csv(responses, filename=None):
    """Export questionnaire responses to CSV format"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"questionnaire_responses_{timestamp}.csv"

    # Load questionnaire structure to get question details
    try:
        with open('questionnaire.json', 'r', encoding='utf-8') as f:
            questionnaire_data = json.load(f)
        questions = questionnaire_data['questionnaire']['questions']
    except FileNotFoundError:
        print("Error: questionnaire.json not found")
        return

    # Create question mapping
    question_map = {q['id']: q for q in questions}

    # Prepare CSV data
    csv_data = []
    headers = ['Question ID', 'Category', 'Question', 'Response', 'Required']

    for question_id, response in responses.items():
        if question_id in question_map:
            question = question_map[question_id]
            # Handle multiple choice responses (lists)
            if isinstance(response, list):
                response_text = ', '.join(response)
            else:
                response_text = str(response)

            csv_data.append([
                question_id,
                question.get('category', ''),
                question['question'],
                response_text,
                'Yes' if question.get('required', False) else 'No'
            ])

    # Write to CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(csv_data)

    print(f"Responses exported to {filename}")
    return filename

def export_responses_to_json(responses, filename=None):
    """Export questionnaire responses to JSON format"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"questionnaire_responses_{timestamp}.json"

    # Add metadata
    export_data = {
        'export_timestamp': datetime.now().isoformat(),
        'total_responses': len(responses),
        'responses': responses
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"Responses exported to {filename}")
    return filename

def analyze_responses(responses):
    """Basic analysis of questionnaire responses"""
    analysis = {
        'total_questions_answered': len(responses),
        'completion_rate': 0,
        'categories_covered': set(),
        'key_insights': []
    }

    # Load questionnaire to get required questions
    try:
        with open('questionnaire.json', 'r', encoding='utf-8') as f:
            questionnaire_data = json.load(f)
        questions = questionnaire_data['questionnaire']['questions']
        total_required = sum(1 for q in questions if q.get('required', False))

        # Calculate completion rate
        required_answered = 0
        for question in questions:
            if question.get('required', False) and question['id'] in responses:
                required_answered += 1

        analysis['completion_rate'] = (required_answered / total_required * 100) if total_required > 0 else 100

        # Collect categories
        for question in questions:
            if question['id'] in responses:
                analysis['categories_covered'].add(question.get('category', 'Uncategorized'))

        analysis['categories_covered'] = list(analysis['categories_covered'])

        # Generate insights
        if 'monthly_income' in responses:
            analysis['key_insights'].append(f"Monthly income reported: {responses['monthly_income']}")

        if 'employment_status' in responses:
            analysis['key_insights'].append(f"Employment status: {responses['employment_status']}")

        if 'financial_goals' in responses:
            analysis['key_insights'].append(f"Financial goals: {responses['financial_goals']}")

    except FileNotFoundError:
        analysis['error'] = "Could not load questionnaire.json for analysis"

    return analysis

# Example usage
if __name__ == "__main__":
    # Example session data (in real usage, this would come from Flask session)
    example_session = {
        'questionnaire_responses': {
            'full_name': 'João Silva',
            'email': 'joao@example.com',
            'marital_status': 'Married / Casado(a)',
            'employment_status': 'Employed / Empregado(a)',
            'monthly_income': '5000',
            'financial_goals': 'Buy a house / Comprar uma casa'
        }
    }

    responses = load_questionnaire_responses(example_session)

    # Export to different formats
    csv_file = export_responses_to_csv(responses)
    json_file = export_responses_to_json(responses)

    # Analyze responses
    analysis = analyze_responses(responses)
    print("\nAnalysis Results:")
    print(f"Completion Rate: {analysis['completion_rate']:.1f}%")
    print(f"Categories Covered: {', '.join(analysis['categories_covered'])}")
    print("Key Insights:")
    for insight in analysis['key_insights']:
        print(f"  - {insight}")