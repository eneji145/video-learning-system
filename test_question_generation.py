# test_question_generation.py
from app.utils.question_generator import QuestionGenerator

def test_question_generation():
    generator = QuestionGenerator()
    
    # Sample text from an educational video
    sample_text = """
    Machine learning is a subfield of artificial intelligence that focuses on developing systems that can learn from data.
    Supervised learning is a type of machine learning where models are trained on labeled data.
    Unsupervised learning, on the other hand, works with unlabeled data to find patterns and structures.
    The third main category is reinforcement learning, where agents learn to make decisions by receiving rewards or penalties.
    """
    
    # Generate questions
    questions = generator.generate_from_text(
        text=sample_text,
        video_id="test_video_id",
        timestamp_start=10.5,
        timestamp_end=60.2,
        num_questions=2
    )
    
    # Print the generated questions
    print(f"Generated {len(questions)} questions:")
    for i, question in enumerate(questions):
        print(f"\nQuestion {i+1}:")
        print(f"ID: {question.get('question_id')}")
        print(f"Text: {question.get('question_text')}")
        print("Options:")
        for option in question.get('options'):
            print(f"  {option.get('id')}: {option.get('text')}")
        print(f"Correct Answer: {question.get('correct_answer')}")
        print(f"Explanation: {question.get('explanation')}")
        print(f"Timestamp: {question.get('timestamp_start')} - {question.get('timestamp_end')}")

if __name__ == "__main__":
    test_question_generation()