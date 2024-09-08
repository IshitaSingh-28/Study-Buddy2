from flask import Flask, render_template, request, flash, redirect, url_for
from flask_bootstrap import Bootstrap
import spacy
from collections import Counter
import random
from PyPDF2 import PdfReader

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages
Bootstrap(app)

# Load English tokenizer, tagger, parser, NER, and word vectors
nlp = spacy.load("en_core_web_sm")

def generate_mcqs(text, num_questions=5):
    if not text:
        return []

    # Process the text with spaCy
    doc = nlp(text)

    # Extract sentences from the text
    sentences = [sent.text for sent in doc.sents]

    # Ensure that the number of questions does not exceed the number of sentences
    num_questions = min(num_questions, len(sentences))

    # Randomly select sentences to form questions
    selected_sentences = random.sample(sentences, num_questions)

    # Initialize list to store generated MCQs
    mcqs = []

    # Generate MCQs for each selected sentence
    for sentence in selected_sentences:
        # Process the sentence with spaCy
        sent_doc = nlp(sentence)

        # Extract entities (nouns) from the sentence
        nouns = [token.text for token in sent_doc if token.pos_ == "NOUN"]

        # Ensure there are enough nouns to generate MCQs
        if len(nouns) < 1:
            continue

        # Count the occurrence of each noun
        noun_counts = Counter(nouns)

        # Select the most common noun as the subject of the question
        if noun_counts:
            subject = noun_counts.most_common(1)[0][0]

            # Generate the question stem
            question_stem = sentence.replace(subject, "______")

            # Generate answer choices
            answer_choices = [subject]

            # Collect distractors from the entire text
            all_nouns = [token.text for token in doc if token.pos_ == "NOUN" and token.text != subject]
            distractors = list(set(all_nouns))

            # Ensure there are at least three distractors
            if len(distractors) >= 3:
                distractors = random.sample(distractors, 3)
            else:
                distractors += ["[Distractor]"] * (3 - len(distractors))

            # Add distractors to answer choices
            answer_choices += distractors

            # Shuffle the answer choices
            random.shuffle(answer_choices)

            # Append the generated MCQ to the list
            correct_answer = chr(65 + answer_choices.index(subject))  # Convert index to letter
            mcqs.append((question_stem, answer_choices, correct_answer))

    return mcqs

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'files[]' not in request.files or len(request.files.getlist('files[]')[0].filename) == 0:
            flash('No file uploaded. Please upload a PDF or TXT file.')
            return redirect(request.url)

        text = ""

        files = request.files.getlist('files[]')
        for file in files:
            if file.filename.endswith('.pdf'):
                # Process PDF file
                text += process_pdf(file)
            elif file.filename.endswith('.txt'):
                # Process text file
                text += file.read().decode('utf-8')
            else:
                flash(f'Unsupported file type: {file.filename}')
                return redirect(request.url)

        # Get the selected number of questions from the dropdown menu
        num_questions = int(request.form.get('num_questions', 5))

        mcqs = generate_mcqs(text, num_questions=num_questions)  # Pass the selected number of questions
        mcqs_with_index = [(i + 1, mcq) for i, mcq in enumerate(mcqs)]
        correct_answers = [mcq[2] for mcq in mcqs]  # Extract correct answers
        return render_template('mcqs.html', mcqs=mcqs_with_index, correct_answers=correct_answers)

    return render_template('index.html')

def process_pdf(file):
    text = ""
    pdf_reader = PdfReader(file)
    for page_num in range(len(pdf_reader.pages)):
        page_text = pdf_reader.pages[page_num].extract_text()
        text += page_text
    return text

if __name__ == '__main__':
    app.run(debug=True)
