# app/utils/subtitle_parser.py
import pysrt
import webvtt
from pathlib import Path

class SubtitleParser:
    def __init__(self):
        self.supported_formats = ['srt', 'vtt']
    
    def parse(self, file_path):
        """Parse subtitle file and return structured data
        
        Args:
            file_path (str): Path to the subtitle file
            
        Returns:
            list: List of subtitle segments with text and timestamps
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()[1:]
        
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported subtitle format: {file_extension}")
        
        if file_extension == 'srt':
            return self._parse_srt(file_path)
        elif file_extension == 'vtt':
            return self._parse_vtt(file_path)
    
    def _parse_srt(self, file_path):
        """Parse SRT subtitle file"""
        subs = pysrt.open(file_path)
        segments = []
        
        for sub in subs:
            segment = {
                'index': sub.index,
                'text': sub.text,
                'start_time': sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds / 1000,
                'end_time': sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000,
                'start_time_str': str(sub.start),
                'end_time_str': str(sub.end)
            }
            segments.append(segment)
        
        return segments
    
    def _parse_vtt(self, file_path):
        """Parse VTT subtitle file"""
        segments = []
        for i, caption in enumerate(webvtt.read(file_path)):
            # Parse the timestamp strings to seconds
            start_parts = caption.start.split(':')
            end_parts = caption.end.split(':')
            
            if len(start_parts) == 3:  # HH:MM:SS.mmm format
                start_time = float(start_parts[0]) * 3600 + float(start_parts[1]) * 60 + float(start_parts[2])
                end_time = float(end_parts[0]) * 3600 + float(end_parts[1]) * 60 + float(end_parts[2])
            else:  # MM:SS.mmm format
                start_time = float(start_parts[0]) * 60 + float(start_parts[1])
                end_time = float(end_parts[0]) * 60 + float(end_parts[1])
            
            segment = {
                'index': i + 1,
                'text': caption.text,
                'start_time': start_time,
                'end_time': end_time,
                'start_time_str': caption.start,
                'end_time_str': caption.end
            }
            segments.append(segment)
        
        return segments
    
    def group_by_topic(self, segments, window_size=5):
        """Group subtitle segments into potential topic chunks
        
        Args:
            segments (list): List of subtitle segments
            window_size (int): Number of segments to group together
            
        Returns:
            list: List of grouped segments
        """
        groups = []
        
        for i in range(0, len(segments), window_size):
            chunk = segments[i:i + window_size]
            
            if len(chunk) > 0:
                group = {
                    'start_index': chunk[0]['index'],
                    'end_index': chunk[-1]['index'],
                    'start_time': chunk[0]['start_time'],
                    'end_time': chunk[-1]['end_time'],
                    'text': ' '.join([segment['text'] for segment in chunk]),
                    'segments': chunk
                }
                groups.append(group)
        
        return groups