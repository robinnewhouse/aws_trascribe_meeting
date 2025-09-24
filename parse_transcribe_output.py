import re

def function(transcript):
    """Parse transcript and return clean speaker-separated text."""
    pattern = r"'content':\s*'([^']+)'.*?'speaker_label':\s*'(spk_\d+)'"
    matches = re.findall(pattern, transcript)
    
    if not matches:
        return "Failed to parse transcript."
    
    # Group by speaker
    current_speaker = None
    current_text = []
    result = []
    
    for content, speaker in matches:
        if content in '.,?!;:':
            if current_text:
                current_text[-1] += content
            continue
            
        if speaker != current_speaker and current_text:
            result.append(f"{current_speaker}: {' '.join(current_text)}")
            current_text = []
            
        current_speaker = speaker
        current_text.append(content)
    
    if current_text:
        result.append(f"{current_speaker}: {' '.join(current_text)}")
    
    return '\n'.join(result)