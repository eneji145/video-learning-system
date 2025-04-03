# app/utils/question_generator.py
import os
import json
import random
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class QuestionGenerator:
    def __init__(self):
        # Define different types of questions
        self.question_types = {
            "multiple_choice": "Multiple choice questions with 4 options",
            "fill_in_the_blank": "Fill in the blank questions with a missing key term",
            "short_answer": "Short answer questions requiring a brief explanation",
            "mixed": "A mixture of different question types"
        }
    
    def _create_prompt_for_type(self, text, num_questions, question_type):
        """Create a prompt based on the question type"""
        base_prompt = f"""
        You are an expert educator creating educational questions based on video content.
        
        Based on the following educational content, generate {num_questions} substantive questions.
        The questions should test deep understanding of key concepts and be valuable for learning.
        
        EDUCATIONAL CONTENT:
        {text}
        """
        
        if question_type == "multiple_choice":
            return base_prompt + """
            CREATE MULTIPLE CHOICE QUESTIONS:
            1. Focus on concepts that are central to understanding the material
            2. Provide 4 options (A, B, C, D) that are all plausible but with only one correct answer
            3. Include a brief explanation for why the correct answer is right
            
            Format your response as a JSON array of question objects with the following structure:
            {
                "questions": [
                    {
                        "type": "multiple_choice",
                        "question_text": "The question here",
                        "options": [
                            {"id": "A", "text": "First option"},
                            {"id": "B", "text": "Second option"},
                            {"id": "C", "text": "Third option"},
                            {"id": "D", "text": "Fourth option"}
                        ],
                        "correct_answer": "A",
                        "explanation": "Why A is the correct answer"
                    }
                ]
            }
            """
        
        elif question_type == "fill_in_the_blank":
            return base_prompt + """
            CREATE FILL IN THE BLANK QUESTIONS:
            1. Identify key terms or concepts from the content
            2. Create sentences with these key terms removed and replaced with a blank
            3. The blank should be for a single word or short phrase that is clearly defined in the content
            4. Include the correct answer and an explanation of why it's correct
            
            Format your response as a JSON array of question objects with the following structure:
            {
                "questions": [
                    {
                        "type": "fill_in_the_blank",
                        "question_text": "A sentence with a _____ that needs to be filled.",
                        "correct_answer": "word",
                        "explanation": "Explanation of why this answer is correct"
                    }
                ]
            }
            """
        
        elif question_type == "short_answer":
            return base_prompt + """
            CREATE SHORT ANSWER QUESTIONS:
            1. Create questions that require brief explanations (1-3 sentences)
            2. Focus on "why" and "how" questions that test understanding
            3. Include an example of a correct answer that would receive full marks
            4. Provide key points that must be included in a correct answer
            
            Format your response as a JSON array of question objects with the following structure:
            {
                "questions": [
                    {
                        "type": "short_answer",
                        "question_text": "A question requiring a brief explanation",
                        "sample_answer": "An example of a good answer",
                        "key_points": ["Point 1 that must be mentioned", "Point 2 that must be mentioned"],
                        "explanation": "What makes a good answer to this question"
                    }
                ]
            }
            """
        
        elif question_type == "mixed":
            return base_prompt + """
            CREATE A MIX OF DIFFERENT QUESTION TYPES:
            Include a balanced mixture of:
            - Multiple choice questions (with 4 options)
            - Fill in the blank questions
            - Short answer questions
            
            Format your response as a JSON array of question objects with the following structures:
            {
                "questions": [
                    {
                        "type": "multiple_choice",
                        "question_text": "A multiple choice question",
                        "options": [
                            {"id": "A", "text": "First option"},
                            {"id": "B", "text": "Second option"},
                            {"id": "C", "text": "Third option"},
                            {"id": "D", "text": "Fourth option"}
                        ],
                        "correct_answer": "A",
                        "explanation": "Why A is correct"
                    },
                    {
                        "type": "fill_in_the_blank",
                        "question_text": "A sentence with a _____ that needs to be filled.",
                        "correct_answer": "word",
                        "explanation": "Explanation of why this answer is correct"
                    },
                    {
                        "type": "short_answer",
                        "question_text": "A question requiring a brief explanation",
                        "sample_answer": "An example of a good answer",
                        "key_points": ["Point 1 that must be mentioned", "Point 2 that must be mentioned"],
                        "explanation": "What makes a good answer to this question"
                    }
                ]
            }
            """
        
        else:
            # Default to multiple choice if an invalid type is specified
            return self._create_prompt_for_type(text, num_questions, "multiple_choice")
    
    def generate_from_text(self, text, video_id, timestamp_start, timestamp_end, num_questions=2, question_type="multiple_choice"):
        """Generate questions based on the specified type
        
        Args:
            text (str): The text content to generate questions from
            video_id (str): The ID of the video this content belongs to
            timestamp_start (float): Start timestamp in seconds
            timestamp_end (float): End timestamp in seconds
            num_questions (int): Number of questions to generate
            question_type (str): Type of questions to generate
            
        Returns:
            list: List of generated question objects
        """
        try:
            # Get the appropriate prompt based on question type
            prompt = self._create_prompt_for_type(text, num_questions, question_type)
            
            # Call OpenAI API to generate questions
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert educator creating educational questions based on video content."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            questions = result.get("questions", [])
            
            # Add metadata to each question
            for i, question in enumerate(questions):
                question["question_id"] = f"{video_id}_{timestamp_start}_{i}"
                question["video_id"] = video_id
                question["timestamp_start"] = timestamp_start
                question["timestamp_end"] = timestamp_end
                
                # Ensure each question has a type field
                if "type" not in question:
                    if "options" in question:
                        question["type"] = "multiple_choice"
                    elif "___" in question.get("question_text", ""):
                        question["type"] = "fill_in_the_blank"
                    else:
                        question["type"] = "short_answer"
            
            return questions
        
        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            return self._generate_fallback_questions(video_id, timestamp_start, timestamp_end, question_type)
    
    def _generate_fallback_questions(self, video_id, timestamp_start, timestamp_end, question_type):
        """Generate fallback questions if the API call fails"""
        fallback_questions = []
        
        if question_type in ["multiple_choice", "mixed"]:
            fallback_questions.append({
                "type": "multiple_choice",
                "question_id": f"{video_id}_{timestamp_start}_0",
                "video_id": video_id,
                "timestamp_start": timestamp_start,
                "timestamp_end": timestamp_end,
                "question_text": "What is the main concept discussed in this segment?",
                "options": [
                    {"id": "A", "text": "Basic principles and terminology"},
                    {"id": "B", "text": "Advanced implementation details"},
                    {"id": "C", "text": "Historical context and development"},
                    {"id": "D", "text": "Comparison with alternative approaches"}
                ],
                "correct_answer": "A",
                "explanation": "The segment focuses primarily on introducing basic principles and terminology."
            })
        
        if question_type in ["fill_in_the_blank", "mixed"]:
            fallback_questions.append({
                "type": "fill_in_the_blank",
                "question_id": f"{video_id}_{timestamp_start}_1",
                "video_id": video_id,
                "timestamp_start": timestamp_start,
                "timestamp_end": timestamp_end,
                "question_text": "The main topic discussed in this segment is _____.",
                "correct_answer": "important concept",
                "explanation": "This segment introduces an important concept central to understanding the topic."
            })
        
        if question_type in ["short_answer", "mixed"]:
            fallback_questions.append({
                "type": "short_answer",
                "question_id": f"{video_id}_{timestamp_start}_2",
                "video_id": video_id,
                "timestamp_start": timestamp_start,
                "timestamp_end": timestamp_end,
                "question_text": "Explain the main concept introduced in this segment.",
                "sample_answer": "The main concept involves understanding the fundamental principles discussed in this segment.",
                "key_points": ["fundamental principles", "main concept"],
                "explanation": "A good answer should identify the main concept and explain its importance."
            })
        
        # Return a subset of the fallback questions based on the requested type
        if question_type == "multiple_choice":
            return fallback_questions[:1]
        elif question_type == "fill_in_the_blank":
            return fallback_questions[1:2]
        elif question_type == "short_answer":
            return fallback_questions[2:3]
        else:
            return fallback_questions