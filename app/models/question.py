# app/models/question.py
class Question:
    def __init__(self, question_id, video_id, timestamp_start, timestamp_end, 
                 question_text, options, correct_answer, explanation):
        self.question_id = question_id
        self.video_id = video_id
        self.timestamp_start = timestamp_start
        self.timestamp_end = timestamp_end
        self.question_text = question_text
        self.options = options
        self.correct_answer = correct_answer
        self.explanation = explanation
    
    def to_dict(self):
        """Convert question object to dictionary"""
        return {
            'question_id': self.question_id,
            'video_id': self.video_id,
            'timestamp_start': self.timestamp_start,
            'timestamp_end': self.timestamp_end,
            'question_text': self.question_text,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a Question object from a dictionary"""
        return cls(
            question_id=data.get('question_id'),
            video_id=data.get('video_id'),
            timestamp_start=data.get('timestamp_start'),
            timestamp_end=data.get('timestamp_end'),
            question_text=data.get('question_text'),
            options=data.get('options'),
            correct_answer=data.get('correct_answer'),
            explanation=data.get('explanation')
        )