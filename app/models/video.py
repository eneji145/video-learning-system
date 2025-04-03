# app/models/video.py
from datetime import datetime

class Video:
    def __init__(self, video_id, title, file_path, subtitle_path=None, duration=None):
        self.video_id = video_id
        self.title = title
        self.file_path = file_path
        self.subtitle_path = subtitle_path
        self.duration = duration
        self.created_at = datetime.now()
        self.subtitle_segments = []
        self.topic_chunks = []
        self.questions = []
    
    def to_dict(self):
        """Convert video object to dictionary"""
        return {
            'video_id': self.video_id,
            'title': self.title,
            'file_path': self.file_path,
            'subtitle_path': self.subtitle_path,
            'duration': self.duration,
            'created_at': self.created_at.isoformat(),
            'subtitle_segments_count': len(self.subtitle_segments),
            'topic_chunks_count': len(self.topic_chunks),
            'questions_count': len(self.questions)
        }
    
    def add_subtitle_segments(self, segments):
        """Add parsed subtitle segments to the video"""
        self.subtitle_segments = segments
    
    def add_topic_chunks(self, chunks):
        """Add topic chunks to the video"""
        self.topic_chunks = chunks