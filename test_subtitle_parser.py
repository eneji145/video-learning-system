# test_subtitle_parser.py
from app.utils.subtitle_parser import SubtitleParser

def test_subtitle_parser():
    parser = SubtitleParser()
    
    # Replace with the path to your test subtitle file
    test_file = 'path/to/your/test/subtitle.srt'
    
    try:
        segments = parser.parse(test_file)
        print(f"Successfully parsed {len(segments)} subtitle segments")
        
        # Print the first few segments
        for i, segment in enumerate(segments[:5]):
            print(f"Segment {i+1}:")
            print(f"  Text: {segment['text']}")
            print(f"  Start Time: {segment['start_time_str']} ({segment['start_time']} seconds)")
            print(f"  End Time: {segment['end_time_str']} ({segment['end_time']} seconds)")
            print()
        
        # Test grouping
        chunks = parser.group_by_topic(segments)
        print(f"Grouped into {len(chunks)} topic chunks")
        
        # Print the first few chunks
        for i, chunk in enumerate(chunks[:3]):
            print(f"Chunk {i+1}:")
            print(f"  Start: {chunk['start_time']} seconds")
            print(f"  End: {chunk['end_time']} seconds")
            print(f"  Text: {chunk['text'][:100]}...")
            print()
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_subtitle_parser()