# app/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from dotenv import load_dotenv
from app.utils.subtitle_parser import SubtitleParser
from app.utils.question_generator import QuestionGenerator
from app.utils.feedback_generator import FeedbackGenerator
from app.models.video import Video
from app.models.database import Database
from app.models.question import Question
import requests
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("youtube-transcript-api not installed. YouTube transcripts won't be available.")
    print("Install with: pip install youtube-transcript-api")
    YouTubeTranscriptApi = None

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize components
db = Database()
subtitle_parser = SubtitleParser()
question_generator = QuestionGenerator()
feedback_generator = FeedbackGenerator()

def is_youtube_url(url):
    """Check if a URL is a YouTube URL"""
    youtube_patterns = [
        "youtube.com/watch",
        "youtu.be/"
    ]
    return url and any(pattern in url for pattern in youtube_patterns)

def extract_youtube_id(youtube_url):
    """Extract YouTube video ID from URL"""
    youtube_id = None
    
    if 'youtube.com/watch' in youtube_url:
        youtube_id = youtube_url.split('v=')[1].split('&')[0] if 'v=' in youtube_url else None
    elif 'youtu.be/' in youtube_url:
        youtube_id = youtube_url.split('youtu.be/')[1].split('?')[0]
    
    return youtube_id

def generate_unique_question_id(video_id, timestamp, sequence_number):
    """Generate a unique question ID that includes a sequence number"""
    return f"{video_id}_{timestamp}_{sequence_number}"

@app.route('/api/videos', methods=['GET'])
def get_videos():
    """Get all videos"""
    videos = db.get_all_videos()
    return jsonify(videos)

@app.route('/api/videos/<video_id>', methods=['GET'])
def get_video(video_id):
    """Get a specific video by ID"""
    video = db.get_video_by_id(video_id)
    if video:
        return jsonify(video)
    return jsonify({'error': 'Video not found'}), 404

@app.route('/api/videos', methods=['POST'])
def add_video():
    """Add a new video with subtitle file"""
    data = request.json
    
    # Create a new video object
    video_id = str(uuid.uuid4())
    
    video = Video(
        video_id=video_id,
        title=data.get('title', 'Untitled Video'),
        file_path=data.get('file_path', ''),
        subtitle_path=data.get('subtitle_path', None),
        duration=data.get('duration', None)
    )
    
    # Parse subtitle file if provided and not a YouTube video
    if video.subtitle_path and os.path.exists(video.subtitle_path) and not is_youtube_url(video.file_path):
        try:
            # Parse subtitles
            segments = subtitle_parser.parse(video.subtitle_path)
            video.add_subtitle_segments(segments)
            
            # Group segments into topic chunks
            chunks = subtitle_parser.group_by_topic(segments)
            video.add_topic_chunks(chunks)
        except Exception as e:
            return jsonify({'error': f'Error parsing subtitles: {str(e)}'}), 400
    
    # Save to database
    db.add_video(video.to_dict())
    
    return jsonify(video.to_dict()), 201

def get_context_for_timestamp(video, timestamp):
    """Get relevant context from video segments near the timestamp"""
    relevant_segments = []
    timestamp = float(timestamp)  # Ensure timestamp is a float
    
    # For YouTube videos, try to get transcript segments
    if is_youtube_url(video.get('file_path')):
        try:
            if YouTubeTranscriptApi is None:
                raise ImportError("YouTube transcript API not installed")
                
            youtube_id = extract_youtube_id(video.get('file_path'))
            if not youtube_id:
                raise ValueError("Could not extract YouTube video ID")
                
            transcript_list = YouTubeTranscriptApi.get_transcript(youtube_id)
            
            # Find segments around the timestamp (30 seconds before and after)
            for item in transcript_list:
                item_start = item['start']
                item_end = item['start'] + item['duration']
                
                if (abs(item_start - timestamp) < 30 or 
                    abs(item_end - timestamp) < 30 or
                    (item_start <= timestamp and item_end >= timestamp)):
                    relevant_segments.append(item['text'])
        except Exception as e:
            print(f"Error getting YouTube transcript for context: {str(e)}")
    
    # For regular videos with subtitle segments
    elif video.get('subtitle_segments'):
        for segment in video.get('subtitle_segments'):
            segment_start = float(segment.get('start_time', 0))
            segment_end = float(segment.get('end_time', 0))
            
            # Check if segment is within 30 seconds of the timestamp
            if ((abs(segment_start - timestamp) < 30 or 
                abs(segment_end - timestamp) < 30) or
                (segment_start <= timestamp and segment_end >= timestamp)):
                relevant_segments.append(segment.get('text', ''))
    
    # If we couldn't find any segments, return a generic message
    if not relevant_segments:
        return f"No specific context available for timestamp {timestamp} in this video."
    
    # Join all relevant segments
    context = " ".join(relevant_segments)
    
    return context

@app.route('/api/videos/<video_id>/ask-question', methods=['POST'])
def ask_question(video_id):
    """Answer a question about a video at a specific timestamp"""
    print(f"Received ask-question request for video {video_id}")
    data = request.json
    question = data.get('question')
    timestamp = data.get('timestamp')
    
    print(f"Question: {question}")
    print(f"Timestamp: {timestamp}")
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    try:
        # Get the video from the database
        video = db.get_video_by_id(video_id)
        if not video:
            print(f"Video {video_id} not found")
            return jsonify({'error': 'Video not found'}), 404
        
        print(f"Found video: {video.get('title')}")
        
        # Get context from video segments near the timestamp
        context = get_context_for_timestamp(video, timestamp)
        print(f"Context length: {len(context)}")
        
        # Create a prompt for ChatGPT
        prompt = f"""
        Based on the following context from a video titled '{video.get('title')}' at timestamp {timestamp} seconds:
        
        {context}
        
        Please answer this question: {question}
        
        Provide a concise and helpful answer based only on the information in the context. If the context doesn't contain enough information to answer the question accurately, acknowledge this limitation in your response.
        """
        
        print("Calling OpenAI API...")
        # Call the OpenAI API using the existing client
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using the same model as your question generator
            messages=[
                {"role": "system", "content": "You are a helpful assistant answering questions about educational videos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        # Extract the answer
        answer = response.choices[0].message.content
        print(f"Received answer from OpenAI: {answer[:100]}...")  # Print first 100 chars
        
        return jsonify({
            'answer': answer
        })
    
    except Exception as e:
        print(f"Error answering question: {str(e)}")
        import traceback
        traceback.print_exc()  # Print the full stack trace
        return jsonify({'error': str(e)}), 500

@app.route('/api/videos/<video_id>/subtitles', methods=['GET'])
def get_subtitles(video_id):
    """Get subtitles for a specific video"""
    video = db.get_video_by_id(video_id)
    if not video:
        return jsonify({'error': 'Video not found'}), 404
    
    # For YouTube videos, try to fetch transcript
    if is_youtube_url(video.get('file_path')):
        try:
            if YouTubeTranscriptApi is None:
                return jsonify({'error': 'YouTube transcript API not installed'}), 500
                
            youtube_id = extract_youtube_id(video.get('file_path'))
            if not youtube_id:
                return jsonify({'error': 'Could not extract YouTube video ID'}), 400
                
            transcript_list = YouTubeTranscriptApi.get_transcript(youtube_id)
            segments = []
            for i, item in enumerate(transcript_list):
                segment = {
                    'index': i + 1,
                    'text': item['text'],
                    'start_time': item['start'],
                    'end_time': item['start'] + item['duration'],
                    'start_time_str': str(item['start']),
                    'end_time_str': str(item['start'] + item['duration'])
                }
                segments.append(segment)
            
            return jsonify(segments)
        except Exception as e:
            return jsonify({'error': f'Error fetching YouTube transcript: {str(e)}'}), 500
    
    # For regular videos with subtitle files
    if not video.get('subtitle_path'):
        return jsonify({'error': 'No subtitles available for this video'}), 404
    
    try:
        segments = subtitle_parser.parse(video.get('subtitle_path'))
        return jsonify(segments)
    except Exception as e:
        return jsonify({'error': f'Error parsing subtitles: {str(e)}'}), 500

@app.route('/api/videos/<video_id>/generate-questions', methods=['POST'])
def generate_questions(video_id):
    """Generate questions for a video"""
    video = db.get_video_by_id(video_id)
    if not video:
        return jsonify({'error': 'Video not found'}), 404
    
    # Get question type and count preferences from request data
    data = request.json or {}
    question_type = data.get('question_type', 'multiple_choice')
    question_count = data.get('question_count', 10)
    
    # Ensure question count is within valid range
    try:
        question_count = int(question_count)
        if question_count < 10:
            question_count = 10
        elif question_count > 20:
            question_count = 20
    except (ValueError, TypeError):
        question_count = 10
    
    # Validate question type
    valid_types = ['multiple_choice', 'fill_in_the_blank', 'short_answer', 'mixed']
    if question_type not in valid_types:
        question_type = 'multiple_choice'  # Default to multiple choice
    
    # First, remove any existing questions for this video to avoid duplicates
    try:
        db.delete_questions_for_video(video_id)
    except Exception as e:
        print(f"Error deleting existing questions: {str(e)}")
        # Continue even if deletion fails
    
    # Counter for unique question IDs
    question_counter = 0
    
    # Check if this is a YouTube video
    if is_youtube_url(video.get('file_path')):
        try:
            if YouTubeTranscriptApi is None:
                raise ImportError("YouTube transcript API not installed")
                
            # Extract YouTube video ID
            youtube_id = extract_youtube_id(video.get('file_path'))
            if not youtube_id:
                raise ValueError("Could not extract YouTube video ID")
                
            # Fetch transcript using youtube_transcript_api
            transcript_list = YouTubeTranscriptApi.get_transcript(youtube_id)
            
            # Convert transcript to subtitle segments format
            segments = []
            for i, item in enumerate(transcript_list):
                segment = {
                    'index': i + 1,
                    'text': item['text'],
                    'start_time': item['start'],
                    'end_time': item['start'] + item['duration'],
                    'start_time_str': str(item['start']),
                    'end_time_str': str(item['start'] + item['duration'])
                }
                segments.append(segment)
            
            # Group segments into topic chunks
            chunks = subtitle_parser.group_by_topic(segments)
            
            # Select evenly distributed chunks from video to generate questions
            generated_questions = []
            
            # Select evenly distributed chunks to match the requested question count
            if len(chunks) <= question_count:
                # If we have fewer chunks than requested questions, use all of them
                chunk_indices = list(range(len(chunks)))
            else:
                # Select evenly distributed chunks to match the requested question count
                step = len(chunks) // question_count
                chunk_indices = [i * step for i in range(question_count)]
                # Make sure we have exactly question_count indices
                if len(chunk_indices) < question_count:
                    # Add additional indices from the middle or end of the video
                    remaining = question_count - len(chunk_indices)
                    middle_start = len(chunks) // 3
                    for i in range(remaining):
                        if middle_start + i < len(chunks) and middle_start + i not in chunk_indices:
                            chunk_indices.append(middle_start + i)
                        else:
                            # Find any unused index
                            for j in range(len(chunks)):
                                if j not in chunk_indices:
                                    chunk_indices.append(j)
                                    break
                
                # Sort the indices to maintain chronological order
                chunk_indices.sort()
                # Trim to exact count if we somehow got more
                chunk_indices = chunk_indices[:question_count]
            
            # Generate questions for selected chunks
            for idx in chunk_indices:
                if idx < len(chunks):
                    chunk = chunks[idx]
                    questions = question_generator.generate_from_text(
                        text=chunk.get('text'),
                        video_id=video_id,
                        timestamp_start=chunk.get('start_time'),
                        timestamp_end=chunk.get('end_time'),
                        num_questions=1,  # Generate 1 question per chunk
                        question_type=question_type  # Pass the question type
                    )
                    
                    # Ensure each question has a unique ID by appending the counter
                    for q in questions:
                        # Update the question_id to ensure uniqueness
                        q['question_id'] = f"{video_id}_{chunk.get('start_time')}_{question_counter}"
                        question_counter += 1
                    
                    generated_questions.extend(questions)
                    
                    # If we have enough questions, stop generating more
                    if len(generated_questions) >= question_count:
                        break
            
            # If we still need more questions, generate from other parts of the video
            if len(generated_questions) < question_count and len(chunks) > 0:
                remaining = question_count - len(generated_questions)
                # Use chunks we haven't used yet
                unused_indices = [i for i in range(len(chunks)) if i not in chunk_indices]
                
                for i in range(min(remaining, len(unused_indices))):
                    idx = unused_indices[i]
                    chunk = chunks[idx]
                    questions = question_generator.generate_from_text(
                        text=chunk.get('text'),
                        video_id=video_id,
                        timestamp_start=chunk.get('start_time'),
                        timestamp_end=chunk.get('end_time'),
                        num_questions=1,
                        question_type=question_type
                    )
                    
                    for q in questions:
                        q['question_id'] = f"{video_id}_{chunk.get('start_time')}_{question_counter}"
                        question_counter += 1
                    
                    generated_questions.extend(questions)
            
            # Ensure we don't exceed the requested question count
            generated_questions = generated_questions[:question_count]
            
            # Print debug info
            print(f"Generated {len(generated_questions)} questions for video {video_id}")
            
            # Save questions to database
            db.add_questions(generated_questions)
            
            return jsonify({
                'success': True,
                'questions_generated': len(generated_questions),
                'questions': generated_questions
            })
            
        except Exception as e:
            # If we can't get the transcript, fall back to generic questions
            print(f"Error getting YouTube transcript: {str(e)}")
            
            title = video.get('title', '')
            
            # Generate dummy questions based on the selected question type
            dummy_questions = []
            
            for i in range(question_count):  # Generate exactly question_count dummy questions
                start_time = 30.0 * i
                end_time = start_time + 20.0
                
                # Create a question based on question type
                if question_type == 'multiple_choice' or (question_type == 'mixed' and i % 3 == 0):
                    question = {
                        "type": "multiple_choice",
                        "question_id": f"{video_id}_{start_time}_{question_counter}",
                        "video_id": video_id,
                        "timestamp_start": start_time,
                        "timestamp_end": end_time,
                        "question_text": f"What is the main focus of this section about {title}?",
                        "options": [
                            {"id": "A", "text": f"Basic principles of {title}"},
                            {"id": "B", "text": f"Advanced implementation of {title}"},
                            {"id": "C", "text": f"Historical context of {title}"},
                            {"id": "D", "text": f"Applications of {title}"}
                        ],
                        "correct_answer": "A",
                        "explanation": f"This section focuses on the basic principles of {title}."
                    }
                elif question_type == 'fill_in_the_blank' or (question_type == 'mixed' and i % 3 == 1):
                    question = {
                        "type": "fill_in_the_blank",
                        "question_id": f"{video_id}_{start_time}_{question_counter}",
                        "video_id": video_id,
                        "timestamp_start": start_time,
                        "timestamp_end": end_time,
                        "question_text": f"The main concept discussed in this section is _____.",
                        "correct_answer": title,
                        "explanation": f"This section introduces the concept of {title}."
                    }
                else:  # short_answer or mixed (i % 3 == 2)
                    question = {
                        "type": "short_answer",
                        "question_id": f"{video_id}_{start_time}_{question_counter}",
                        "video_id": video_id,
                        "timestamp_start": start_time,
                        "timestamp_end": end_time,
                        "question_text": f"Explain the key concepts related to {title} discussed in this section.",
                        "sample_answer": f"This section covers the fundamental concepts of {title}, including its basic principles and applications.",
                        "key_points": [f"Basic principles of {title}", f"Applications of {title}"],
                        "explanation": f"A good answer should identify the main concepts of {title} discussed in this section."
                    }
                
                question_counter += 1
                dummy_questions.append(question)
            
            # Save questions to database
            db.add_questions(dummy_questions)
            
            return jsonify({
                'success': True,
                'questions_generated': len(dummy_questions),
                'questions': dummy_questions
            })
    
    # For regular videos with subtitle content
    if not video.get('topic_chunks'):
        return jsonify({'error': 'No content chunks available for this video'}), 400
    
    generated_questions = []
    topic_chunks = video.get('topic_chunks')
    
    # Determine how many chunks to use
    if len(topic_chunks) <= question_count:
        # If we have fewer chunks than requested questions, use all of them
        selected_chunks = topic_chunks
    else:
        # Select evenly distributed chunks to match the requested question count
        step = len(topic_chunks) // question_count
        selected_indices = [i * step for i in range(question_count)]
        # Ensure we don't exceed the array bounds
        selected_indices = [i for i in selected_indices if i < len(topic_chunks)]
        selected_chunks = [topic_chunks[i] for i in selected_indices]
    
    # Generate questions for each selected chunk
    for chunk in selected_chunks:
        # Generate questions for each chunk
        questions = question_generator.generate_from_text(
            text=chunk.get('text'),
            video_id=video_id,
            timestamp_start=chunk.get('start_time'),
            timestamp_end=chunk.get('end_time'),
            num_questions=1,  # Generate 1 question per chunk
            question_type=question_type  # Pass the question type
        )
        
        # Ensure each question has a unique ID
        for q in questions:
            q['question_id'] = f"{video_id}_{chunk.get('start_time')}_{question_counter}"
            question_counter += 1
        
        generated_questions.extend(questions)
        
        # If we have enough questions, stop generating more
        if len(generated_questions) >= question_count:
            break
    
    # Ensure we have exactly the requested number of questions
    if len(generated_questions) < question_count and len(topic_chunks) > 0:
        # Generate additional questions from other chunks
        remaining = question_count - len(generated_questions)
        # Try to use different chunks
        used_indices = set([topic_chunks.index(chunk) for chunk in selected_chunks if chunk in topic_chunks])
        available_indices = [i for i in range(len(topic_chunks)) if i not in used_indices]
        
        # If we've used all chunks, just reuse some
        if not available_indices:
            available_indices = list(range(len(topic_chunks)))
        
        for i in range(min(remaining, len(available_indices))):
            chunk = topic_chunks[available_indices[i]]
            questions = question_generator.generate_from_text(
                text=chunk.get('text'),
                video_id=video_id,
                timestamp_start=chunk.get('start_time'),
                timestamp_end=chunk.get('end_time'),
                num_questions=1,
                question_type=question_type
            )
            
            for q in questions:
                q['question_id'] = f"{video_id}_{chunk.get('start_time')}_{question_counter}"
                question_counter += 1
            
            generated_questions.extend(questions)
    
    # Ensure we don't exceed the requested question count
    generated_questions = generated_questions[:question_count]
    
    # Save questions to database
    db.add_questions(generated_questions)
    
    return jsonify({
        'success': True,
        'questions_generated': len(generated_questions),
        'questions': generated_questions
    })

@app.route('/api/videos/<video_id>/questions', methods=['GET'])
def get_questions(video_id):
    """Get all questions for a video"""
    questions = db.get_questions_for_video(video_id)
    return jsonify(questions)

@app.route('/api/questions/<question_id>', methods=['GET'])
def get_question(question_id):
    """Get a specific question by ID"""
    all_questions = db.get_all_questions()
    for question in all_questions:
        if question.get('question_id') == question_id:
            return jsonify(question)
    return jsonify({'error': 'Question not found'}), 404

@app.route('/api/videos/<video_id>', methods=['DELETE'])
def delete_video(video_id):
    """Delete a specific video and its questions"""
    try:
        # Get the database
        db = Database()
        
        # First check if the video exists
        video = db.get_video_by_id(video_id)
        if not video:
            return jsonify({'error': 'Video not found'}), 404
        
        # Delete all questions associated with this video
        db.delete_questions_for_video(video_id)
        
        # Delete the video itself
        # Add this method to your Database class
        # This is implemented below
        db.delete_video(video_id)
        
        return jsonify({'success': True, 'message': 'Video deleted successfully'})
    except Exception as e:
        print(f"Error deleting video: {str(e)}")
        return jsonify({'error': f'Failed to delete video: {str(e)}'}), 500

@app.route('/api/questions/<question_id>/verify', methods=['POST'])
def verify_answer(question_id):
    """Verify if an answer is correct and provide feedback"""
    data = request.json
    user_answer = data.get('answer')
    
    if user_answer is None:  # Allow empty string answers but not missing ones
        return jsonify({'error': 'No answer provided'}), 400
    
    # Get the question
    all_questions = db.get_all_questions()
    question = None
    for q in all_questions:
        if q.get('question_id') == question_id:
            question = q
            break
    
    if not question:
        return jsonify({'error': 'Question not found'}), 404
    
    # Get context text from video
    video_id = question.get('video_id')
    timestamp_start = question.get('timestamp_start')
    timestamp_end = question.get('timestamp_end')
    
    context_text = None
    video = db.get_video_by_id(video_id)
    if video and video.get('subtitle_segments'):
        # Find segments that overlap with the question timestamp
        relevant_segments = []
        for segment in video.get('subtitle_segments'):
            if (segment.get('start_time') <= timestamp_end and 
                segment.get('end_time') >= timestamp_start):
                relevant_segments.append(segment.get('text'))
        
        if relevant_segments:
            context_text = ' '.join(relevant_segments)
    
    # Generate feedback based on the question type
    feedback_result = feedback_generator.generate_feedback(
        question=question,
        user_answer=user_answer,
        original_explanation=question.get('explanation'),
        context_text=context_text
    )
    
    return jsonify(feedback_result)

if __name__ == '__main__':
    app.run(debug=True)