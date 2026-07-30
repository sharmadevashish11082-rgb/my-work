import re
import string

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "while", "of", "at", "by", "for",
    "with", "about", "against", "between", "into", "through", "during", "before", "after",
    "to", "from", "in", "out", "on", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "can", "will",
    "just", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "doesn", "don", "doesn", "didn", "may", "might", "must",
    "could", "should", "would"
}


def tokenize_sentences(text):
    text = text.strip().replace("\n", " ")
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [part.strip() for part in parts if part.strip()]


def normalize_words(text):
    text = text.lower()
    text = text.translate(str.maketrans(string.punctuation, ' ' * len(string.punctuation)))
    return [word for word in text.split() if word and word not in STOPWORDS]


def summarize_notes(notes, max_sentences=3):
    sentences = tokenize_sentences(notes)
    if not sentences:
        return "No notes provided."

    word_freq = {}
    for sentence in sentences:
        for word in normalize_words(sentence):
            word_freq[word] = word_freq.get(word, 0) + 1

    if not word_freq:
        return ' '.join(sentences[:max_sentences])

    sentence_scores = []
    for idx, sentence in enumerate(sentences):
        score = sum(word_freq.get(word, 0) for word in normalize_words(sentence))
        sentence_scores.append((score, idx, sentence))

    best = sorted(sentence_scores, key=lambda item: (-item[0], item[1]))[:max_sentences]
    best = sorted(best, key=lambda item: item[1])
    return ' '.join(sentence for _, _, sentence in best)


def extract_definition_sentences(sentences):
    patterns = [r'(.+?)\s+is\s+(.+)', r'(.+?)\s+refers to\s+(.+)', r'(.+?)\s+means\s+(.+)']
    results = []
    for sentence in sentences:
        for pattern in patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match and len(match.groups()) >= 2:
                subject = match.group(1).strip(' .')
                definition = match.group(2).strip(' .')
                if subject and definition:
                    results.append((subject, definition, sentence))
    return results


def generate_quiz(notes, num_questions=5):
    sentences = tokenize_sentences(notes)
    if not sentences:
        return [
            {
                'question': 'Add some notes first before generating a quiz.',
                'answer': ''
            }
        ]

    candidate_defs = extract_definition_sentences(sentences)
    quiz = []

    for subject, definition, _ in candidate_defs:
        if len(quiz) >= num_questions:
            break
        question = f"What is {subject.strip()}?"
        answer = definition.strip()
        quiz.append({'question': question, 'answer': answer})

    if len(quiz) < num_questions:
        for sentence in sentences:
            if len(quiz) >= num_questions:
                break
            words = normalize_words(sentence)
            if len(words) > 6:
                question = f"Explain the following: {sentence}"
                quiz.append({'question': question, 'answer': sentence})

    if not quiz:
        quiz.append({'question': 'Unable to create quiz from notes.', 'answer': ''})

    return quiz[:num_questions]


def explain_concept(concept, notes=None):
    if not concept:
        return "Please provide a concept to explain."

    if notes:
        sentences = tokenize_sentences(notes)
        matches = [s for s in sentences if concept.lower() in s.lower()]
        if matches:
            return ' '.join(matches[:2])

    return f"I could not find '{concept}' in the provided notes. Generally, {concept} is a topic that can be described in terms of its main ideas and use cases."


def main():
    print('AI Study Assistant')
    print('Features:')
    print('- Summarize notes')
    print('- Generate quizzes')
    print('- Explain concepts')
    print()

    notes = ''
    while True:
        print('Select an option:')
        print('1. Enter or update notes')
        print('2. Summarize notes')
        print('3. Generate quiz')
        print('4. Explain a concept')
        print('5. Exit')
        choice = input('> ').strip()

        if choice == '1':
            print('Paste your notes. End with an empty line:')
            lines = []
            while True:
                line = input()
                if line == '':
                    break
                lines.append(line)
            notes = '\n'.join(lines).strip()
            print('Notes stored.\n')

        elif choice == '2':
            print('\nSummary:')
            print(summarize_notes(notes))
            print()

        elif choice == '3':
            quiz = generate_quiz(notes)
            print('\nQuiz:')
            for idx, item in enumerate(quiz, start=1):
                print(f"{idx}. {item['question']}")
                if item['answer']:
                    print(f"   Answer: {item['answer']}")
            print()

        elif choice == '4':
            concept = input('Enter concept to explain: ').strip()
            print('\nExplanation:')
            print(explain_concept(concept, notes))
            print()

        elif choice == '5':
            print('Goodbye.')
            break

        else:
            print('Invalid option. Choose 1-5.\n')


if __name__ == '__main__':
    main()
