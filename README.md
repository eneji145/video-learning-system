# Interactive Video Learning System

An AI-enhanced educational platform that transforms passive video consumption into interactive learning experiences through automated question generation, personalized feedback, and temporal navigation.

## Overview

The Interactive Video Learning System addresses key limitations in traditional educational videos by incorporating:

- **AI-generated assessment questions** based on video content
- **Real-time question asking** for clarification during viewing
- **Temporal navigation** that links questions to specific video segments
- **Personalized feedback** with contextual explanations

The system works with both locally hosted videos and YouTube content, making it applicable to a wide range of educational materials.

## Research Background

This project was developed as part of MSc research investigating how AI-enhanced features can improve learning outcomes in video-based education. Research findings demonstrated:

- 27.8% improvement in learning outcomes compared to 14.5% with traditional video
- High usability ratings (SUS score of 82.3)
- Significant increase in learner engagement and active learning behaviors

## Features

### For Learners

- **Interactive Video Player**: Pause, navigate, and interact with educational content
- **Multiple Question Types**: Multiple-choice, fill-in-blank, and short answer questions
- **Real-time Questioning**: Ask questions about specific video content with AI-generated answers
- **Contextual Feedback**: Receive explanations for incorrect answers with links to relevant content
- **Temporal Navigation**: Jump directly to video segments related to questions or topics
- **Responsive Design**: Accessible on various devices with light/dark mode support

### For Content Creators

- **Automated Question Generation**: AI-powered creation of assessment items
- **Subtitle Processing**: Extract and analyze video transcripts for content understanding
- **YouTube Integration**: Work with existing YouTube educational content
- **Flexible Question Configuration**: Customize question types and quantity

## Technology Stack

### Frontend
- React.js for component-based UI
- ReactPlayer for video playback
- CSS3 with responsive design and theme support

### Backend
- Flask (Python) for API endpoints and business logic
- OpenAI API for natural language processing and content generation
- YouTube Transcript API for subtitle extraction

### Data Processing
- Subtitle parsing and content segmentation
- Natural language processing for question generation
- Answer validation and feedback generation

## Installation

### Prerequisites
- Python 3.9+
- Node.js 14+
- OpenAI API key
- (Optional) YouTube API key for enhanced YouTube integration

### Backend Setup
1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies
4. Create a .env file with your API keys
5. Start the Flask server

### Frontend Setup
1. Navigate to the frontend directory
2. Install dependencies
3. Start the development server
4. Access the application at http://localhost:3000

## Usage

### Adding Videos
1. From the home page, click "Add New Video"
2. Enter a title and video URL (YouTube links or local file paths)
3. Submit the form to add the video to the library

### Learning from Videos
1. Select a video from the home page
2. Choose question type and quantity preferences
3. Start the quiz to begin the interactive learning experience
4. Answer questions as they appear
5. Use the "Review in Video" feature to revisit content related to questions
6. Pause the video at any time to ask clarification questions

## Contributors

- Ali Patrick Eneji - MSc Researcher, University of Dundee

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Research supervised by Dr. Michael Crabb, University of Dundee
- Built upon research in educational technology, AI-enhanced learning, and video-based education
