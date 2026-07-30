




import json
import os
import random

LEADERBOARD_FILE = "leaderboard.json"

QUIZ_CATEGORIES = {
    "Science": [
        {
            "question": "What planet is known as the Red Planet?",
            "choices": ["Earth", "Mars", "Jupiter", "Venus"],
            "answer": "Mars"
        },
        {
            "question": "What is the chemical symbol for water?",
            "choices": ["H2O", "O2", "CO2", "NaCl"],
            "answer": "H2O"
        },
        {
            "question": "What gas do plants absorb from the atmosphere?",
            "choices": ["Oxygen", "Nitrogen", "Carbon dioxide", "Hydrogen"],
            "answer": "Carbon dioxide"
        }
    ],
    "History": [
        {
            "question": "Who was the first President of the United States?",
            "choices": ["George Washington", "Thomas Jefferson", "Abraham Lincoln", "John Adams"],
            "answer": "George Washington"
        },
        {
            "question": "The Great Wall is located in which country?",
            "choices": ["India", "China", "Japan", "Egypt"],
            "answer": "China"
        },
        {
            "question": "Which year did the World War II end?",
            "choices": ["1942", "1945", "1950", "1939"],
            "answer": "1945"
        }
    ],
    "Sports": [
        {
            "question": "How many players are on a soccer team on the field?",
            "choices": ["9", "10", "11", "12"],
            "answer": "11"
        },
        {
            "question": "In which sport is the term 'home run' used?",
            "choices": ["Basketball", "Cricket", "Baseball", "Football"],
            "answer": "Baseball"
        },
        {
            "question": "Which sport uses a racket and shuttlecock?",
            "choices": ["Tennis", "Badminton", "Squash", "Ping Pong"],
            "answer": "Badminton"
        }
    ]
}


def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, IOError):
        return []


def save_leaderboard(leaderboard):
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as file:
        json.dump(leaderboard, file, indent=2)


def display_categories():
    print("\nAvailable Categories:")
    for index, category in enumerate(QUIZ_CATEGORIES.keys(), start=1):
        print(f"  {index}. {category}")


def get_category_choice():
    categories = list(QUIZ_CATEGORIES.keys())
    while True:
        display_categories()
        choice = input("Select a category number: ").strip()
        if choice.isdigit():
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(categories):
                return categories[choice_index]
        print("Invalid selection. Please try again.")


def ask_questions(category):
    questions = QUIZ_CATEGORIES[category].copy()
    random.shuffle(questions)
    score = 0
    total = min(5, len(questions))
    print(f"\nStarting quiz in '{category}' with {total} questions.")

    for i in range(total):
        item = questions[i]
        print(f"\nQuestion {i + 1}: {item['question']}")
        for idx, choice in enumerate(item['choices'], start=1):
            print(f"  {idx}. {choice}")

        while True:
            answer = input("Your answer (number): ").strip()
            if answer.isdigit():
                choice_index = int(answer) - 1
                if 0 <= choice_index < len(item['choices']):
                    selected = item['choices'][choice_index]
                    break
            print("Invalid choice. Try again.")

        if selected == item['answer']:
            print("Correct!")
            score += 1
        else:
            print(f"Wrong. The correct answer was: {item['answer']}")

    return score, total


def update_leaderboard(name, score, total, leaderboard):
    entry = {
        "name": name,
        "score": score,
        "total": total,
        "percent": round((score / total) * 100, 1)
    }
    leaderboard.append(entry)
    leaderboard.sort(key=lambda x: (-x["score"], -x["percent"]))
    save_leaderboard(leaderboard)
    return leaderboard


def show_leaderboard(leaderboard):
    if not leaderboard:
        print("\nLeaderboard is empty. Take a quiz to add your score.")
        return
    print("\nLeaderboard:")
    for index, entry in enumerate(leaderboard[:10], start=1):
        print(f"  {index}. {entry['name']} - {entry['score']}/{entry['total']} ({entry['percent']}%)")


def main():
    print("Welcome to the Quiz Application")
    name = input("Enter your name: ").strip() or "Player"
    leaderboard = load_leaderboard()

    while True:
        print("\nMenu:")
        print("  1. Take a quiz")
        print("  2. View leaderboard")
        print("  3. Quit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            category = get_category_choice()
            score, total = ask_questions(category)
            print(f"\n{name}, your score: {score}/{total}")
            leaderboard = update_leaderboard(name, score, total, leaderboard)
        elif choice == "2":
            show_leaderboard(leaderboard)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose 1, 2, or 3.")


if __name__ == "__main__":
    main()
