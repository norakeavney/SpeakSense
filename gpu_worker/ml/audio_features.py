"""
Audio Feature Extraction Service
Extracts audio-based features per speaker for emotion and bias analysis
"""

import numpy as np
import librosa
import logging

logger = logging.getLogger(__name__)


def extract_audio_features(file_ref, speaker_segments):
    """
    Extract audio features for each speaker from their speech segments.
    
    Args:
        file_ref: Path to the audio file
        speaker_segments: Dict with speaker IDs as keys and list of segment dicts as values
                         Each segment should have 'start' and 'end' times in seconds
    
    Returns:
        Dict with speaker IDs as keys and their audio features as values
    """
    logger.info(f"Extracting audio features from: {file_ref}")
    
    try:
        # Load the full audio file
        y, sr = librosa.load(file_ref, sr=None)
        logger.info(f"Loaded audio: sample_rate={sr}, duration={len(y)/sr:.2f}s")
        
        speaker_features = {}
        
        for speaker_id, segments in speaker_segments.items():
            logger.info(f"Processing {len(segments)} segments for {speaker_id}")
            
            # Extract audio for all segments of this speaker
            speaker_audio = _combine_speaker_segments(y, sr, segments)
            
            if len(speaker_audio) == 0:
                logger.warning(f"No audio data for {speaker_id}")
                continue
            
            # Calculate features for this speaker
            features = _calculate_speaker_audio_features(speaker_audio, sr)
            speaker_features[speaker_id] = features
            
            logger.info(f"{speaker_id} features: pitch={features['avg_pitch']:.1f}Hz, "
                       f"loudness={features['avg_loudness']:.2f}dB")
        
        return speaker_features
    
    except Exception as e:
        logger.error(f"Error extracting audio features: {str(e)}")
        return {}


def _combine_speaker_segments(audio_signal, sample_rate, segments):
    """
    Combine all audio segments for a speaker into one continuous array.
    
    Args:
        audio_signal: Full audio signal array
        sample_rate: Sample rate of the audio
        segments: List of segment dicts with 'start' and 'end' times
    
    Returns:
        Combined numpy array of speaker's audio
    """
    speaker_audio_chunks = []
    
    for segment in segments:
        start_sample = int(segment['start'] * sample_rate)
        end_sample = int(segment['end'] * sample_rate)
        
        # Ensure we don't go out of bounds
        start_sample = max(0, start_sample)
        end_sample = min(len(audio_signal), end_sample)
        
        if end_sample > start_sample:
            speaker_audio_chunks.append(audio_signal[start_sample:end_sample])
    
    if speaker_audio_chunks:
        return np.concatenate(speaker_audio_chunks)
    return np.array([])


def _calculate_speaker_audio_features(audio_segment, sample_rate):
    """
    Calculate audio features for a speaker's audio segment.
    
    Args:
        audio_segment: Audio signal for the speaker
        sample_rate: Sample rate of the audio
    
    Returns:
        Dict of audio features
    """
    features = {}
    
    # === PITCH FEATURES ===
    # Extract fundamental frequency (F0) using piptrack
    pitches, magnitudes = librosa.piptrack(y=audio_segment, sr=sample_rate)
    
    # Get pitch values where magnitude is high (voiced segments)
    pitch_values = []
    for t in range(pitches.shape[1]):
        index = magnitudes[:, t].argmax()
        pitch = pitches[index, t]
        if pitch > 0:  # Only include voiced segments
            pitch_values.append(pitch)
    
    if pitch_values:
        features['avg_pitch'] = float(np.mean(pitch_values))
        features['pitch_std'] = float(np.std(pitch_values))
        features['pitch_range'] = float(np.max(pitch_values) - np.min(pitch_values))
        features['pitch_variation'] = float(np.std(pitch_values) / np.mean(pitch_values)) if np.mean(pitch_values) > 0 else 0.0
    else:
        features['avg_pitch'] = 0.0
        features['pitch_std'] = 0.0
        features['pitch_range'] = 0.0
        features['pitch_variation'] = 0.0
    
    # === LOUDNESS / AMPLITUDE FEATURES ===
    # Calculate RMS energy (root mean square) as a measure of loudness
    rms = librosa.feature.rms(y=audio_segment)[0]
    features['avg_loudness'] = float(20 * np.log10(np.mean(rms) + 1e-10))  # Convert to dB
    features['loudness_std'] = float(np.std(rms))
    features['loudness_range'] = float(np.max(rms) - np.min(rms))
    
    # === ENERGY FEATURES ===
    # Zero crossing rate - indicates noise vs tonal content
    zcr = librosa.feature.zero_crossing_rate(audio_segment)[0]
    features['avg_zero_crossing_rate'] = float(np.mean(zcr))
    
    # Spectral centroid - brightness of the sound
    spectral_centroids = librosa.feature.spectral_centroid(y=audio_segment, sr=sample_rate)[0]
    features['avg_spectral_centroid'] = float(np.mean(spectral_centroids))
    features['spectral_centroid_std'] = float(np.std(spectral_centroids))
    
    # === SPEAKING RATE INDICATORS ===
    # Estimate speaking rate from onset detection (syllables/phonemes)
    onset_env = librosa.onset.onset_strength(y=audio_segment, sr=sample_rate)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sample_rate)
    duration = len(audio_segment) / sample_rate
    features['onset_rate'] = len(onsets) / duration if duration > 0 else 0.0  # onsets per second
    
    # === VOICE QUALITY INDICATORS ===
    # Spectral rolloff - frequency below which 85% of energy is contained
    spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_segment, sr=sample_rate)[0]
    features['avg_spectral_rolloff'] = float(np.mean(spectral_rolloff))
    
    # Spectral bandwidth
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio_segment, sr=sample_rate)[0]
    features['avg_spectral_bandwidth'] = float(np.mean(spectral_bandwidth))
    
    return features


def interpret_audio_features(speaker_features):
    """
    Add human-readable interpretations of audio features.
    
    Args:
        speaker_features: Dict with speaker IDs and their audio features
    
    Returns:
        Dict with added interpretation fields
    """
    for speaker_id, features in speaker_features.items():
        interpretations = {}
        
        # Pitch interpretation
        avg_pitch = features.get('avg_pitch', 0)
        if avg_pitch > 0:
            if avg_pitch < 150:
                interpretations['pitch_level'] = 'low'
            elif avg_pitch < 200:
                interpretations['pitch_level'] = 'medium'
            else:
                interpretations['pitch_level'] = 'high'
        else:
            interpretations['pitch_level'] = 'unknown'
        
        # Pitch variation interpretation (monotone vs expressive)
        pitch_var = features.get('pitch_variation', 0)
        if pitch_var < 0.1:
            interpretations['expressiveness'] = 'monotone'
        elif pitch_var < 0.2:
            interpretations['expressiveness'] = 'moderate'
        else:
            interpretations['expressiveness'] = 'expressive'
        
        # Loudness interpretation
        avg_loudness = features.get('avg_loudness', -60)
        if avg_loudness > -10:
            interpretations['volume_level'] = 'loud'
        elif avg_loudness > -20:
            interpretations['volume_level'] = 'moderate'
        else:
            interpretations['volume_level'] = 'quiet'
        
        # Energy interpretation
        zcr = features.get('avg_zero_crossing_rate', 0)
        if zcr > 0.1:
            interpretations['voice_quality'] = 'energetic/noisy'
        elif zcr > 0.05:
            interpretations['voice_quality'] = 'balanced'
        else:
            interpretations['voice_quality'] = 'calm/tonal'
        
        features['interpretations'] = interpretations
    
    return speaker_features


# Example usage format:
# speaker_segments = {
#     'SPEAKER_00': [
#         {'start': 0.5, 'end': 3.2},
#         {'start': 5.1, 'end': 8.7}
#     ],
#     'SPEAKER_01': [
#         {'start': 3.5, 'end': 4.9}
#     ]
# }
# features = extract_audio_features('audio.wav', speaker_segments)
# features_with_interp = interpret_audio_features(features)
