# test_feedback_generator.py
from app.utils.feedback_generator import FeedbackGenerator

def test_feedback_generation():
    generator = FeedbackGenerator()
    
    # Sample question
    question = {
        'question_id': 'test_question',
        'question_text': 'What is machine learning?',
        'options': [
            {'id': 'A', 'text': 'A type of computer hardware'},
            {'id': 'B', 'text': 'A field of study that gives computers the ability to learn without being explicitly programmed'},
            {'id': 'C', 'text': 'A programming language'},
            {'id': 'D', 'text': 'A database management system'}
        ],
        'correct_answer': 'B'
    }
    
    # Test correct answer
    correct_feedback = generator.generate_feedback(
        question=question,
        user_answer='B',
        is_correct=True,
        original_explanation='Machine learning is a field of study focused on algorithms that can learn from data.',
        context_text='Machine learning is a subfield of artificial intelligence that focuses on developing systems that can learn from data without being explicitly programmed.'
    )
    
    # Test incorrect answer
    incorrect_feedback = generator.generate_feedback(
        question=question,
        user_answer='A',
        is_correct=False,
        original_explanation='Machine learning is a field of study focused on algorithms that can learn from data.',
        context_text='Machine learning is a subfield of artificial intelligence that focuses on developing systems that can learn from data without being explicitly programmed.'
    )
    
    print("Feedback for correct answer:")
    print(correct_feedback)
    print("\nFeedback for incorrect answer:")
    print(incorrect_feedback)

if __name__ == "__main__":
    test_feedback_generation()