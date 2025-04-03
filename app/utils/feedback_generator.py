# app/utils/feedback_generator.py
import os
import random
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class FeedbackGenerator:
    def __init__(self):
        # Variety of feedback starters for incorrect answers
        self.incorrect_starters = [
            "Not quite.",
            "That's not correct.",
            "Your answer isn't quite right.",
            "That's a common misconception.",
            "You're on the right track, but not quite there.",
            "Close, but not quite correct.",
            "That's not the right answer.",
            "This isn't the correct option.",
            "Good attempt, but that's not right.",
            "That's not accurate in this case.",
            "That's a reasonable guess, but it's not correct.",
            "That's not the answer we're looking for.",
            "That option isn't correct.",
            "Your understanding needs a small adjustment here."
        ]
        
        # Variety of feedback starters for correct answers
        self.correct_starters = [
            "Excellent!",
            "That's correct!",
            "Perfect answer!",
            "Well done!",
            "You got it!",
            "Spot on!",
            "That's exactly right!",
            "Great job!",
            "You're absolutely right!",
            "Correct!",
            "That's the right answer!",
            "You've understood this well!",
            "That's perfect!",
            "You're showing good understanding here!"
        ]
    
    def generate_feedback(self, question, user_answer, original_explanation, context_text=None):
        """Generate personalized feedback for a user's answer
        
        Args:
            question (dict): The question object
            user_answer (str): The user's answer
            original_explanation (str): The explanation provided with the question
            context_text (str, optional): Additional context from the video transcript
            
        Returns:
            dict: Feedback information including correctness and explanation
        """
        # Determine the question type and handle accordingly
        question_type = question.get("type", "multiple_choice")
        
        if question_type == "multiple_choice":
            is_correct = user_answer == question.get("correct_answer")
            return self._generate_multiple_choice_feedback(question, user_answer, is_correct, original_explanation, context_text)
        
        elif question_type == "fill_in_the_blank":
            # For fill in the blank, do more fuzzy matching
            user_answer_normalized = user_answer.strip().lower()
            correct_answer_normalized = question.get("correct_answer", "").strip().lower()
            
            # Check for exact match or close match
            is_correct = user_answer_normalized == correct_answer_normalized
            
            # If it's not an exact match, check if it's a substring or if correct answer is a substring
            if not is_correct:
                if user_answer_normalized in correct_answer_normalized or correct_answer_normalized in user_answer_normalized:
                    is_partial = True
                    return self._generate_fill_in_blank_feedback(question, user_answer, "partial", original_explanation, context_text)
            
            return self._generate_fill_in_blank_feedback(question, user_answer, "correct" if is_correct else "incorrect", original_explanation, context_text)
        
        elif question_type == "short_answer":
            # For short answers, use AI to evaluate the answer against key points
            return self._evaluate_short_answer(question, user_answer, original_explanation, context_text)
        
        else:
            # Default to multiple choice behavior
            is_correct = user_answer == question.get("correct_answer")
            return self._generate_multiple_choice_feedback(question, user_answer, is_correct, original_explanation, context_text)
    
    def _generate_multiple_choice_feedback(self, question, user_answer, is_correct, original_explanation, context_text):
        """Generate feedback for multiple choice questions"""
        try:
            # Get the user's selected option text
            user_option_text = next((opt.get('text') for opt in question.get('options', []) if opt.get('id') == user_answer), "Unknown option")
            
            # Get the correct option text
            correct_option_text = next((opt.get('text') for opt in question.get('options', []) if opt.get('id') == question.get('correct_answer')), "Unknown option")
            
            # Extract the topic from the question for additional resources
            question_topic = question.get('question_text', '')[:50]  # Use first 50 chars to determine topic
            
            # Create a prompt for feedback generation with additional resources
            prompt = f"""
            You are an educational assistant providing feedback on a multiple-choice question.
            
            Question: {question.get('question_text')}
            
            The user selected: "{user_option_text}"
            
            The correct answer is: "{correct_option_text}"
            
            Is the user correct? {"Yes" if is_correct else "No"}
            
            Original explanation: {original_explanation}
            
            Additional context from the video: {context_text or 'Not available'}
            
            Please provide personalized feedback that:
            1. Uses a natural, conversational tone
            2. Does NOT start with generic phrases like "That's not quite right" or "That's incorrect"
            3. Explains why the correct answer is right and (if applicable) why the user's choice was wrong
            4. Connects the explanation to relevant concepts from the video
            5. Is encouraging and supportive
            6. Is concise (2-4 sentences)
            
            Additionally, suggest 2-3 high-quality web resources (with URLs) where the user can learn more about this topic.
            These should be reputable sources like educational websites, documentation, or well-known blogs.
            
            Format your response as a JSON object with the following structure:
            {{
                "feedback": "Your detailed, conversational feedback here",
                "additional_resources": [
                    {{
                        "title": "Resource Title 1",
                        "url": "https://example.com/resource1",
                        "description": "Brief description of this resource"
                    }},
                    {{
                        "title": "Resource Title 2",
                        "url": "https://example.com/resource2",
                        "description": "Brief description of this resource"
                    }}
                ]
            }}
            
            IMPORTANT:
            - Do not use numbered lists or points in your feedback
            - Do not use phrases like "Feedback:" or other labels
            - Vary your language and avoid repetitive phrasing
            - Don't just restate the original explanation - provide additional insight
            - For educational resources, select a diverse set of high-quality links
            - Make sure URLs are valid and point to legitimate educational resources
            """
            
            # Call OpenAI API for feedback
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an educational assistant providing natural, varied, and conversational feedback on quiz answers."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            feedback = result.get("feedback", "")
            additional_resources = result.get("additional_resources", [])
            
            # Check if the feedback is empty or too short
            if not feedback or len(feedback) < 20:
                # Fall back to template-based feedback
                feedback = self._generate_template_feedback(is_correct, original_explanation, question.get('correct_answer'), user_option_text, correct_option_text)
                additional_resources = self._generate_fallback_resources(question_topic)
            
            return {
                "is_correct": is_correct,
                "correct_answer": question.get('correct_answer'),
                "explanation": original_explanation,
                "enhanced_feedback": feedback,
                "additional_resources": additional_resources,
                "question_id": question.get('question_id'),
                "timestamp_start": question.get('timestamp_start'),
                "timestamp_end": question.get('timestamp_end'),
                "video_id": question.get('video_id')
            }
            
        except Exception as e:
            print(f"Error generating feedback for multiple choice: {str(e)}")
            # Fall back to simple template
            feedback = self._generate_template_feedback(
                is_correct, 
                original_explanation, 
                question.get('correct_answer', ''), 
                "your answer", 
                "the correct answer"
            )
            
            fallback_resources = self._generate_fallback_resources(question.get('question_text', '')[:50])
            
            return {
                "is_correct": is_correct,
                "correct_answer": question.get('correct_answer'),
                "explanation": original_explanation,
                "enhanced_feedback": feedback,
                "additional_resources": fallback_resources,
                "question_id": question.get('question_id'),
                "timestamp_start": question.get('timestamp_start'),
                "timestamp_end": question.get('timestamp_end'),
                "video_id": question.get('video_id')
            }
    
    def _generate_fill_in_blank_feedback(self, question, user_answer, result_type, original_explanation, context_text):
        """Generate feedback for fill in the blank questions"""
        try:
            correct_answer = question.get('correct_answer', '')
            
            # Extract the topic from the question for additional resources
            question_topic = question.get('question_text', '')[:50]  # Use first 50 chars to determine topic
            
            prompt = f"""
            You are an educational assistant providing feedback on a fill-in-the-blank question.
            
            Question: {question.get('question_text')}
            
            The user answered: "{user_answer}"
            
            The correct answer is: "{correct_answer}"
            
            Result: {"Correct" if result_type == "correct" else "Partial match" if result_type == "partial" else "Incorrect"}
            
            Original explanation: {original_explanation}
            
            Additional context from the video: {context_text or 'Not available'}
            
            Please provide personalized feedback that:
            1. Uses a natural, conversational tone
            2. Acknowledges if the answer was correct, partially correct, or incorrect
            3. Explains the correct answer and any nuances in wording that might be important
            4. Connects the explanation to relevant concepts from the video
            5. Is encouraging and supportive
            6. Is concise (2-4 sentences)
            
            Additionally, suggest 2-3 high-quality web resources (with URLs) where the user can learn more about this topic.
            These should be reputable sources like educational websites, documentation, or well-known blogs.
            
            Format your response as a JSON object with the following structure:
            {{
                "feedback": "Your detailed, conversational feedback here",
                "additional_resources": [
                    {{
                        "title": "Resource Title 1",
                        "url": "https://example.com/resource1",
                        "description": "Brief description of this resource"
                    }},
                    {{
                        "title": "Resource Title 2",
                        "url": "https://example.com/resource2",
                        "description": "Brief description of this resource"
                    }}
                ]
            }}
            """
            
            # Call OpenAI API for feedback
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an educational assistant providing feedback on fill-in-the-blank questions."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            feedback = result.get("feedback", "")
            additional_resources = result.get("additional_resources", [])
            
            is_correct = result_type == "correct"
            
            # If the feedback is missing or too short, use template fallback
            if not feedback or len(feedback) < 20:
                if is_correct:
                    feedback = f"{random.choice(self.correct_starters)} You correctly filled in the blank with '{question.get('correct_answer')}'."
                elif result_type == "partial":
                    feedback = f"Your answer '{user_answer}' is close to the correct answer '{question.get('correct_answer')}'. {original_explanation}"
                else:
                    feedback = f"{random.choice(self.incorrect_starters)} The correct answer is '{question.get('correct_answer')}'. {original_explanation}"
                
                additional_resources = self._generate_fallback_resources(question_topic)
            
            return {
                "is_correct": is_correct,
                "is_partial": result_type == "partial",
                "correct_answer": correct_answer,
                "explanation": original_explanation,
                "enhanced_feedback": feedback,
                "additional_resources": additional_resources,
                "question_id": question.get('question_id'),
                "timestamp_start": question.get('timestamp_start'),
                "timestamp_end": question.get('timestamp_end'),
                "video_id": question.get('video_id')
            }
            
        except Exception as e:
            print(f"Error generating feedback for fill in the blank: {str(e)}")
            
            # Determine if it's correct or partial
            is_correct = result_type == "correct"
            is_partial = result_type == "partial"
            
            if is_correct:
                feedback = f"{random.choice(self.correct_starters)} You correctly filled in the blank with '{question.get('correct_answer')}'."
            elif is_partial:
                feedback = f"Your answer '{user_answer}' is close to the correct answer '{question.get('correct_answer')}'. {original_explanation}"
            else:
                feedback = f"{random.choice(self.incorrect_starters)} The correct answer is '{question.get('correct_answer')}'. {original_explanation}"
            
            fallback_resources = self._generate_fallback_resources(question.get('question_text', '')[:50])
            
            return {
                "is_correct": is_correct,
                "is_partial": is_partial,
                "correct_answer": question.get('correct_answer'),
                "explanation": original_explanation,
                "enhanced_feedback": feedback,
                "additional_resources": fallback_resources,
                "question_id": question.get('question_id'),
                "timestamp_start": question.get('timestamp_start'),
                "timestamp_end": question.get('timestamp_end'),
                "video_id": question.get('video_id')
            }
    
    def _evaluate_short_answer(self, question, user_answer, original_explanation, context_text):
        """Evaluate a short answer response using AI"""
        try:
            key_points = question.get('key_points', [])
            sample_answer = question.get('sample_answer', '')
            
            # Extract the topic from the question for additional resources
            question_topic = question.get('question_text', '')[:50]  # Use first 50 chars to determine topic
            
            # Check if the answer is too short or nonsensical (like "grb")
            if len(user_answer.strip()) < 5 or (user_answer.strip().isalpha() and len(user_answer.strip()) < 4):
                # This is likely a non-serious answer or random characters
                fallback_resources = self._generate_fallback_resources(question_topic)
                
                return {
                    "is_correct": False,
                    "is_partial": False,
                    "score_percentage": 0,  # Give 0% for obviously incorrect/minimal answers
                    "correct_answer": sample_answer,
                    "key_points": key_points,
                    "explanation": original_explanation,
                    "enhanced_feedback": f"Your answer is too brief to assess properly. A good response should include: {', '.join(key_points)}. {original_explanation}",
                    "additional_resources": fallback_resources,
                    "question_id": question.get('question_id'),
                    "timestamp_start": question.get('timestamp_start'),
                    "timestamp_end": question.get('timestamp_end'),
                    "video_id": question.get('video_id')
                }
            
            key_points_text = "\n".join([f"- {point}" for point in key_points])
            
            prompt = f"""
            You are an educational assistant evaluating a short answer response.
            
            Question: {question.get('question_text')}
            
            Student's answer: "{user_answer}"
            
            Sample correct answer: "{sample_answer}"
            
            Key points that should be included:
            {key_points_text}
            
            Original explanation of what makes a good answer: {original_explanation}
            
            Additional context from the video: {context_text or 'Not available'}
            
            Please evaluate the student's answer on a scale of 0-100%, where:
            - 0-10%: Very minimal, irrelevant, or nonsensical answer
            - 11-30%: Missing nearly all key points, major misconceptions
            - 31-50%: Includes at least one key point but has significant gaps
            - 51-70%: Includes some key points with minor misconceptions
            - 71-90%: Includes most key points with minor issues
            - 91-100%: Includes all key points and demonstrates thorough understanding
            
            VERY IMPORTANT: If the answer is very short (less than 10 words) and doesn't address any of the key points, give a score under 20%.
            
            Additionally, suggest 2-3 high-quality web resources (with URLs) where the user can learn more about this topic.
            These should be reputable sources like educational websites, documentation, or well-known blogs.
            
            Format your response as a JSON object with the following structure:
            {{
                "score_percentage": 85,
                "feedback": "Your detailed, conversational feedback here",
                "additional_resources": [
                    {{
                        "title": "Resource Title 1",
                        "url": "https://example.com/resource1",
                        "description": "Brief description of this resource"
                    }},
                    {{
                        "title": "Resource Title 2",
                        "url": "https://example.com/resource2",
                        "description": "Brief description of this resource"
                    }}
                ]
            }}
            """
            
            # Call OpenAI API for evaluation
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an educational assistant evaluating short answer responses."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            score = result.get("score_percentage", 0)
            feedback = result.get("feedback", "")
            additional_resources = result.get("additional_resources", [])
            
            # Determine if it's correct based on score threshold
            is_correct = score >= 75  # Consider 75% or higher as correct
            is_partial = 30 <= score < 75  # Consider 30-74% as partially correct
            
            return {
                "is_correct": is_correct,
                "is_partial": is_partial,
                "score_percentage": score,
                "correct_answer": sample_answer,
                "key_points": key_points,
                "explanation": original_explanation,
                "enhanced_feedback": feedback,
                "additional_resources": additional_resources,
                "question_id": question.get('question_id'),
                "timestamp_start": question.get('timestamp_start'),
                "timestamp_end": question.get('timestamp_end'),
                "video_id": question.get('video_id')
            }
            
        except Exception as e:
            print(f"Error evaluating short answer: {str(e)}")
            
            # Analyze the answer length
            if len(user_answer.strip()) < 5:
                score = 0
                feedback = f"Your answer is too brief. A good response should include: {', '.join(question.get('key_points', []))}. {original_explanation}"
            else:
                # Better fallback scoring - doing basic word matching with key points
                score = 0
                matched_points = 0
                for point in question.get('key_points', []):
                    keywords = [word.lower() for word in point.split() if len(word) > 3]
                    for keyword in keywords:
                        if keyword in user_answer.lower():
                            matched_points += 1
                            break
                
                if matched_points > 0:
                    score = min(70, int(matched_points / len(question.get('key_points', [])) * 60))
                
                feedback = f"Based on keyword matching, your answer addresses approximately {score}% of the key points. A complete answer should include: {', '.join(question.get('key_points', []))}. {original_explanation}"
            
            fallback_resources = self._generate_fallback_resources(question.get('question_text', '')[:50])
            
            return {
                "is_correct": score >= 75,
                "is_partial": 30 <= score < 75,
                "score_percentage": score,
                "correct_answer": question.get('sample_answer', ''),
                "key_points": question.get('key_points', []),
                "explanation": original_explanation,
                "enhanced_feedback": feedback,
                "additional_resources": fallback_resources,
                "question_id": question.get('question_id'),
                "timestamp_start": question.get('timestamp_start'),
                "timestamp_end": question.get('timestamp_end'),
                "video_id": question.get('video_id')
            }
    
    def _generate_template_feedback(self, is_correct, original_explanation, correct_answer_id, user_option_text, correct_option_text):
        """Generate feedback using templates when API call fails"""
        if is_correct:
            starter = random.choice(self.correct_starters)
            return f"{starter} {original_explanation}"
        else:
            starter = random.choice(self.incorrect_starters)
            return f"{starter} The correct answer is {correct_answer_id} ({correct_option_text}). {original_explanation}"
    
    def _generate_fallback_resources(self, topic):
        """Generate fallback resources when API call fails or returns insufficient data"""
        # General educational resources for various topics
        general_resources = [
            {
                "title": "Khan Academy",
                "url": "https://www.khanacademy.org/",
                "description": "Free educational resources across many subjects with video lessons and practice exercises."
            },
            {
                "title": "MIT OpenCourseWare",
                "url": "https://ocw.mit.edu/",
                "description": "Free course materials from MIT covering a wide range of subjects."
            },
            {
                "title": "Coursera",
                "url": "https://www.coursera.org/",
                "description": "Online courses from top universities and companies across many disciplines."
            },
            {
                "title": "edX",
                "url": "https://www.edx.org/",
                "description": "Online courses from leading educational institutions on a variety of topics."
            },
            {
                "title": "MDN Web Docs",
                "url": "https://developer.mozilla.org/",
                "description": "Comprehensive documentation for web technologies and programming."
            },
            {
                "title": "W3Schools",
                "url": "https://www.w3schools.com/",
                "description": "Web development tutorials and reference materials with interactive examples."
            },
            {
                "title": "Digital Ocean Community Tutorials",
                "url": "https://www.digitalocean.com/community/tutorials",
                "description": "Detailed technical tutorials on programming, software, and system administration."
            }
        ]
        
        # Select 2-3 resources at random (different ones each time)
        selected_resources = random.sample(general_resources, min(3, len(general_resources)))
        return selected_resources