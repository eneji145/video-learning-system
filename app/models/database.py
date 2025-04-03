# app/models/database.py
import json
import os
from pathlib import Path

class Database:
    def __init__(self, db_path='app/data'):
        self.db_path = Path(db_path)
        self.videos_file = self.db_path / 'videos.json'
        self.questions_file = self.db_path / 'questions.json'
        
        # Create data directory if it doesn't exist
        os.makedirs(self.db_path, exist_ok=True)
        
        # Initialize database files if they don't exist
        if not self.videos_file.exists():
            with open(self.videos_file, 'w') as f:
                json.dump([], f)
        
        if not self.questions_file.exists():
            with open(self.questions_file, 'w') as f:
                json.dump([], f)
    
    def get_all_videos(self):
        """Get all videos from the database"""
        with open(self.videos_file, 'r') as f:
            return json.load(f)
    
    def get_video_by_id(self, video_id):
        """Get a video by its ID"""
        videos = self.get_all_videos()
        for video in videos:
            if video['video_id'] == video_id:
                return video
        return None
    
    def add_video(self, video_dict):
        """Add a new video to the database"""
        videos = self.get_all_videos()
        videos.append(video_dict)
        with open(self.videos_file, 'w') as f:
            json.dump(videos, f, indent=2)
    
    def update_video(self, video_id, updated_video):
        """Update an existing video in the database"""
        videos = self.get_all_videos()
        for i, video in enumerate(videos):
            if video['video_id'] == video_id:
                videos[i] = updated_video
                break
        
        with open(self.videos_file, 'w') as f:
            json.dump(videos, f, indent=2)
    
    def get_questions_for_video(self, video_id):
        """Get all questions for a specific video"""
        with open(self.questions_file, 'r') as f:
            all_questions = json.load(f)
        
        return [q for q in all_questions if q['video_id'] == video_id]
    
    def get_all_questions(self):
        """Get all questions from the database"""
        with open(self.questions_file, 'r') as f:
            return json.load(f)
    
    def add_questions(self, questions):
        """Add questions to the database"""
        with open(self.questions_file, 'r') as f:
            all_questions = json.load(f)
        
        all_questions.extend(questions)
        
        with open(self.questions_file, 'w') as f:
            json.dump(all_questions, f, indent=2)
    
    def delete_questions_for_video(self, video_id):
        """Delete all questions for a specific video"""
        with open(self.questions_file, 'r') as f:
            all_questions = json.load(f)
        
        # Filter out questions for the specified video
        filtered_questions = [q for q in all_questions if q.get('video_id') != video_id]
        
        # Save the filtered list back to the file
        with open(self.questions_file, 'w') as f:
            json.dump(filtered_questions, f, indent=2)

    def delete_video(self, video_id):
        """Delete a video from the database by its ID"""
        videos = self.get_all_videos()
        
        # Filter out the video to be deleted
        updated_videos = [v for v in videos if v.get('video_id') != video_id]
        
        # If the lengths are the same, the video wasn't found
        if len(videos) == len(updated_videos):
            raise ValueError(f"Video with ID {video_id} not found")
        
        # Write the updated videos list back to the file
        with open(self.videos_file, 'w') as f:
            json.dump(updated_videos, f, indent=2)
        
        return True