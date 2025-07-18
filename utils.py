# utils.py

import csv
from rapidfuzz import process

# This function will load data from 'data/faq_data.csv' and return tools for the chatbot
def create_college_bot(return_questions=False):
    csv_path = 'data/faq_data.csv'
    faq_questions = []
    qa_dict = {}

    # Load questions and answers from the CSV
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            question = row['Question'].strip()
            answer = row['Answer'].strip()
            faq_questions.append(question)
            qa_dict[question] = answer

    # Dummy retriever for fallback (not used much here, but kept if needed later)
    class DummyRetriever:
        def get_relevant_documents(self, query):
            matches = process.extract(query, faq_questions, limit=1, score_cutoff=70)
            if matches:
                top_match = matches[0][0]
                return [type("Doc", (), {"page_content": qa_dict[top_match]})()]
            else:
                return []

    retriever = DummyRetriever()

    if return_questions:
        return retriever, faq_questions, qa_dict
    else:
        return retriever
