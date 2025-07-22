import logging
import asyncio
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import re
from scipy import signal
from scipy.fft import fft

from app.config import settings
from app.database import get_db
from app.models import CallLog, CallDisposition

logger = logging.getLogger(__name__)


class VoicemailState(Enum):
    ANALYZING = "analyzing"
    HUMAN_DETECTED = "human_detected"
    VOICEMAIL_DETECTED = "voicemail_detected"
    BEEP_DETECTED = "beep_detected"
    MESSAGE_RECORDING = "message_recording"
    COMPLETED = "completed"


@dataclass
class AudioAnalysis:
    """Analysis results for audio segment"""
    duration: float
    speech_detected: bool
    silence_duration: float
    continuous_speech_duration: float
    voice_consistency_score: float
    background_noise_level: float
    frequency_analysis: Dict[str, float]
    keywords_detected: List[str]
    beep_probability: float


@dataclass
class VoicemailDetectionResult:
    """Result of voicemail detection analysis"""
    state: VoicemailState
    confidence: float
    human_probability: float
    voicemail_probability: float
    beep_detected: bool
    recommended_action: str
    analysis_details: Dict[str, Any]


class VoicemailDetectionService:
    """
    Advanced voicemail detection service that analyzes audio patterns,
    speech characteristics, and timing to distinguish between human answers
    and voicemail systems.
    """
    
    def __init__(self):
        self.active_detections: Dict[int, Dict[str, Any]] = {}
        
        # Voicemail keyword patterns
        self.voicemail_keywords = [
            "leave a message", "after the tone", "after the beep",
            "not available", "can't come to", "unable to take",
            "please leave", "you have reached", "at the sound",
            "mailbox", "voicemail", "recording", "unavailable",
            "away from", "out of the office", "temporarily unavailable"
        ]
        
        # Human response patterns
        self.human_keywords = [
            "hello", "hi there", "good morning", "good afternoon",
            "speaking", "this is", "how can i help", "what can i do",
            "thanks for calling", "hold on", "just a moment"
        ]
        
        # Beep frequency ranges (Hz) - typical voicemail beeps
        self.beep_frequencies = [
            (800, 1200),   # Common beep range
            (1000, 1500),  # Higher pitched beeps
            (400, 800),    # Lower pitched beeps
        ]
        
    async def start_detection(self, call_log_id: int) -> Dict[str, Any]:
        """Initialize voicemail detection for a call"""
        try:
            self.active_detections[call_log_id] = {
                'state': VoicemailState.ANALYZING,
                'start_time': datetime.utcnow(),
                'audio_segments': [],
                'speech_segments': [],
                'silence_segments': [],
                'total_duration': 0.0,
                'continuous_speech_duration': 0.0,
                'human_indicators': 0,
                'voicemail_indicators': 0,
                'beep_candidates': [],
                'keyword_matches': [],
                'confidence_scores': []
            }
            
            logger.info(f"Started voicemail detection for call {call_log_id}")
            
            return {
                'detection_id': call_log_id,
                'state': VoicemailState.ANALYZING.value,
                'message': 'Voicemail detection started'
            }
            
        except Exception as e:
            logger.error(f"Error starting voicemail detection: {e}")
            raise
    
    async def analyze_audio_chunk(
        self, 
        call_log_id: int, 
        audio_data: bytes,
        transcript: Optional[str] = None
    ) -> VoicemailDetectionResult:
        """Analyze an audio chunk for voicemail characteristics"""
        try:
            if call_log_id not in self.active_detections:
                await self.start_detection(call_log_id)
            
            detection = self.active_detections[call_log_id]
            
            # Convert audio to numpy array for analysis
            audio_array = self._bytes_to_numpy(audio_data)
            
            # Perform audio analysis
            analysis = await self._analyze_audio_segment(audio_array, transcript)
            
            # Update detection state
            detection['audio_segments'].append(analysis)
            detection['total_duration'] += analysis.duration
            
            # Analyze for voicemail patterns
            result = await self._evaluate_voicemail_probability(call_log_id, analysis)
            
            # Update call disposition if confident
            if result.confidence > 0.8:
                await self._update_call_disposition(call_log_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing audio chunk: {e}")
            return VoicemailDetectionResult(
                state=VoicemailState.ANALYZING,
                confidence=0.0,
                human_probability=0.5,
                voicemail_probability=0.5,
                beep_detected=False,
                recommended_action="continue_analysis",
                analysis_details={'error': str(e)}
            )
    
    async def _analyze_audio_segment(
        self, 
        audio_array: np.ndarray, 
        transcript: Optional[str] = None
    ) -> AudioAnalysis:
        """Detailed analysis of audio segment"""
        try:
            duration = len(audio_array) / settings.audio_sample_rate
            
            # Speech detection
            speech_detected = self._detect_speech(audio_array)
            
            # Silence analysis
            silence_duration = self._calculate_silence_duration(audio_array)
            
            # Continuous speech analysis
            continuous_speech = self._analyze_continuous_speech(audio_array)
            
            # Voice consistency (humans vary more, voicemail is consistent)
            voice_consistency = self._calculate_voice_consistency(audio_array)
            
            # Background noise analysis
            background_noise = self._analyze_background_noise(audio_array)
            
            # Frequency analysis for beep detection
            frequency_analysis = self._analyze_frequencies(audio_array)
            
            # Keyword detection from transcript
            keywords_detected = self._detect_keywords(transcript) if transcript else []
            
            # Beep probability
            beep_probability = self._calculate_beep_probability(frequency_analysis)
            
            return AudioAnalysis(
                duration=duration,
                speech_detected=speech_detected,
                silence_duration=silence_duration,
                continuous_speech_duration=continuous_speech,
                voice_consistency_score=voice_consistency,
                background_noise_level=background_noise,
                frequency_analysis=frequency_analysis,
                keywords_detected=keywords_detected,
                beep_probability=beep_probability
            )
            
        except Exception as e:
            logger.error(f"Error in audio analysis: {e}")
            raise
    
    async def _evaluate_voicemail_probability(
        self, 
        call_log_id: int, 
        analysis: AudioAnalysis
    ) -> VoicemailDetectionResult:
        """Evaluate probability of voicemail vs human based on analysis"""
        try:
            detection = self.active_detections[call_log_id]
            
            # Initialize scoring
            human_score = 0.0
            voicemail_score = 0.0
            
            # 1. Duration Analysis (voicemails tend to be longer initial messages)
            if detection['total_duration'] > 15.0:  # > 15 seconds
                voicemail_score += 30
            elif detection['total_duration'] < 5.0:  # < 5 seconds
                human_score += 20
            else:
                human_score += 10
            
            # 2. Continuous Speech Analysis
            if analysis.continuous_speech_duration > 10.0:
                voicemail_score += 25  # Long continuous speech = likely voicemail
            elif analysis.continuous_speech_duration < 3.0:
                human_score += 15  # Short responses = likely human
            
            # 3. Voice Consistency Analysis
            if analysis.voice_consistency_score > 0.8:
                voicemail_score += 20  # Very consistent = recorded message
            elif analysis.voice_consistency_score < 0.5:
                human_score += 20  # Variable = human speech
            
            # 4. Keyword Analysis
            voicemail_keywords_found = [kw for kw in analysis.keywords_detected 
                                       if any(vm_kw in kw.lower() for vm_kw in self.voicemail_keywords)]
            human_keywords_found = [kw for kw in analysis.keywords_detected 
                                   if any(h_kw in kw.lower() for h_kw in self.human_keywords)]
            
            voicemail_score += len(voicemail_keywords_found) * 15
            human_score += len(human_keywords_found) * 15
            
            # 5. Beep Detection
            if analysis.beep_probability > 0.7:
                voicemail_score += 40  # Strong beep signal
                detection['state'] = VoicemailState.BEEP_DETECTED
            
            # 6. Silence Pattern Analysis
            if analysis.silence_duration > 2.0:
                if detection['total_duration'] > 8.0:
                    voicemail_score += 15  # Silence after long speech = end of greeting
                else:
                    human_score += 10  # Early silence = human thinking
            
            # 7. Background Noise Analysis
            if analysis.background_noise_level < 0.1:
                voicemail_score += 10  # Clean recording = voicemail
            else:
                human_score += 5  # Background noise = live environment
            
            # Normalize scores
            total_score = human_score + voicemail_score
            if total_score > 0:
                human_probability = human_score / total_score
                voicemail_probability = voicemail_score / total_score
            else:
                human_probability = voicemail_probability = 0.5
            
            # Determine confidence
            confidence = abs(human_probability - voicemail_probability)
            
            # Determine state
            if voicemail_probability > 0.7 and confidence > 0.4:
                state = VoicemailState.VOICEMAIL_DETECTED
            elif human_probability > 0.7 and confidence > 0.4:
                state = VoicemailState.HUMAN_DETECTED
            elif analysis.beep_probability > 0.7:
                state = VoicemailState.BEEP_DETECTED
            else:
                state = VoicemailState.ANALYZING
            
            # Recommended action
            if state == VoicemailState.HUMAN_DETECTED:
                recommended_action = "continue_conversation"
            elif state == VoicemailState.VOICEMAIL_DETECTED:
                recommended_action = "wait_for_beep"
            elif state == VoicemailState.BEEP_DETECTED:
                recommended_action = "leave_message"
            else:
                recommended_action = "continue_analysis"
            
            return VoicemailDetectionResult(
                state=state,
                confidence=confidence,
                human_probability=human_probability,
                voicemail_probability=voicemail_probability,
                beep_detected=analysis.beep_probability > 0.7,
                recommended_action=recommended_action,
                analysis_details={
                    'human_score': human_score,
                    'voicemail_score': voicemail_score,
                    'duration': detection['total_duration'],
                    'keywords_found': analysis.keywords_detected,
                    'beep_probability': analysis.beep_probability
                }
            )
            
        except Exception as e:
            logger.error(f"Error evaluating voicemail probability: {e}")
            raise
    
    def _bytes_to_numpy(self, audio_data: bytes) -> np.ndarray:
        """Convert audio bytes to numpy array"""
        try:
            # Assuming 16-bit PCM audio
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            # Normalize to [-1, 1]
            return audio_array.astype(np.float32) / 32768.0
        except Exception as e:
            logger.error(f"Error converting audio to numpy: {e}")
            return np.array([])
    
    def _detect_speech(self, audio_array: np.ndarray) -> bool:
        """Detect if speech is present in audio"""
        try:
            # Simple energy-based speech detection
            energy = np.sum(audio_array ** 2)
            threshold = settings.speech_detection_threshold
            return energy > threshold
        except Exception as e:
            logger.error(f"Error in speech detection: {e}")
            return False
    
    def _calculate_silence_duration(self, audio_array: np.ndarray) -> float:
        """Calculate duration of silence in audio"""
        try:
            # Define silence threshold
            silence_threshold = 0.01
            silence_samples = np.sum(np.abs(audio_array) < silence_threshold)
            return silence_samples / settings.audio_sample_rate
        except Exception as e:
            logger.error(f"Error calculating silence duration: {e}")
            return 0.0
    
    def _analyze_continuous_speech(self, audio_array: np.ndarray) -> float:
        """Analyze duration of continuous speech"""
        try:
            # Window-based analysis
            window_size = int(0.1 * settings.audio_sample_rate)  # 100ms windows
            speech_windows = []
            
            for i in range(0, len(audio_array), window_size):
                window = audio_array[i:i+window_size]
                if len(window) > 0:
                    energy = np.sum(window ** 2) / len(window)
                    speech_windows.append(energy > settings.speech_detection_threshold)
            
            # Find longest continuous speech segment
            max_continuous = 0
            current_continuous = 0
            
            for is_speech in speech_windows:
                if is_speech:
                    current_continuous += 1
                else:
                    max_continuous = max(max_continuous, current_continuous)
                    current_continuous = 0
            
            max_continuous = max(max_continuous, current_continuous)
            return max_continuous * 0.1  # Convert windows to seconds
            
        except Exception as e:
            logger.error(f"Error analyzing continuous speech: {e}")
            return 0.0
    
    def _calculate_voice_consistency(self, audio_array: np.ndarray) -> float:
        """Calculate voice consistency score (0-1)"""
        try:
            # Analyze pitch consistency
            # Simple approach: calculate variance in amplitude over time
            window_size = int(0.1 * settings.audio_sample_rate)
            amplitudes = []
            
            for i in range(0, len(audio_array), window_size):
                window = audio_array[i:i+window_size]
                if len(window) > 0:
                    amplitudes.append(np.sqrt(np.mean(window ** 2)))
            
            if len(amplitudes) < 2:
                return 0.5
            
            # Lower variance = more consistent (voicemail)
            variance = np.var(amplitudes)
            consistency = max(0.0, min(1.0, 1.0 - variance * 10))
            return consistency
            
        except Exception as e:
            logger.error(f"Error calculating voice consistency: {e}")
            return 0.5
    
    def _analyze_background_noise(self, audio_array: np.ndarray) -> float:
        """Analyze background noise level"""
        try:
            # Find quiet segments and measure their noise level
            threshold = 0.05
            quiet_segments = audio_array[np.abs(audio_array) < threshold]
            
            if len(quiet_segments) > 0:
                noise_level = np.sqrt(np.mean(quiet_segments ** 2))
                return noise_level
            return 0.0
            
        except Exception as e:
            logger.error(f"Error analyzing background noise: {e}")
            return 0.0
    
    def _analyze_frequencies(self, audio_array: np.ndarray) -> Dict[str, float]:
        """Analyze frequency content of audio"""
        try:
            # Perform FFT
            fft_result = fft(audio_array)
            frequencies = np.fft.fftfreq(len(audio_array), 1/settings.audio_sample_rate)
            magnitudes = np.abs(fft_result)
            
            # Analyze specific frequency ranges
            analysis = {}
            
            # Low frequencies (50-300 Hz) - voice fundamentals
            low_mask = (frequencies >= 50) & (frequencies <= 300)
            analysis['low_freq_energy'] = np.sum(magnitudes[low_mask])
            
            # Mid frequencies (300-3000 Hz) - speech clarity
            mid_mask = (frequencies >= 300) & (frequencies <= 3000)
            analysis['mid_freq_energy'] = np.sum(magnitudes[mid_mask])
            
            # High frequencies (3000+ Hz) - consonants and noise
            high_mask = frequencies >= 3000
            analysis['high_freq_energy'] = np.sum(magnitudes[high_mask])
            
            # Beep frequency analysis
            for i, (low, high) in enumerate(self.beep_frequencies):
                beep_mask = (frequencies >= low) & (frequencies <= high)
                analysis[f'beep_range_{i}'] = np.sum(magnitudes[beep_mask])
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing frequencies: {e}")
            return {}
    
    def _detect_keywords(self, transcript: str) -> List[str]:
        """Detect voicemail and human keywords in transcript"""
        if not transcript:
            return []
        
        transcript_lower = transcript.lower()
        detected = []
        
        # Check voicemail keywords
        for keyword in self.voicemail_keywords:
            if keyword in transcript_lower:
                detected.append(f"voicemail:{keyword}")
        
        # Check human keywords
        for keyword in self.human_keywords:
            if keyword in transcript_lower:
                detected.append(f"human:{keyword}")
        
        return detected
    
    def _calculate_beep_probability(self, frequency_analysis: Dict[str, float]) -> float:
        """Calculate probability of beep presence"""
        try:
            if not frequency_analysis:
                return 0.0
            
            # Look for characteristic beep patterns
            beep_scores = []
            
            for i in range(len(self.beep_frequencies)):
                beep_key = f'beep_range_{i}'
                if beep_key in frequency_analysis:
                    # Normalize by total energy
                    total_energy = (frequency_analysis.get('low_freq_energy', 0) +
                                  frequency_analysis.get('mid_freq_energy', 0) +
                                  frequency_analysis.get('high_freq_energy', 0))
                    
                    if total_energy > 0:
                        beep_ratio = frequency_analysis[beep_key] / total_energy
                        beep_scores.append(beep_ratio)
            
            # Return highest beep probability
            return max(beep_scores) if beep_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating beep probability: {e}")
            return 0.0
    
    async def _update_call_disposition(
        self, 
        call_log_id: int, 
        result: VoicemailDetectionResult
    ):
        """Update call disposition based on detection result"""
        try:
            if result.state == VoicemailState.VOICEMAIL_DETECTED or result.state == VoicemailState.BEEP_DETECTED:
                async with get_db() as db:
                    # Update call log with voicemail disposition
                    call_log = await db.get(CallLog, call_log_id)
                    if call_log:
                        call_log.disposition = CallDisposition.VOICEMAIL
                        call_log.voicemail_detection_confidence = result.confidence
                        call_log.detection_metadata = json.dumps(result.analysis_details)
                        await db.commit()
                        
                        logger.info(f"Updated call {call_log_id} disposition to VOICEMAIL")
                        
        except Exception as e:
            logger.error(f"Error updating call disposition: {e}")
    
    async def get_voicemail_message_template(
        self, 
        call_log_id: int, 
        campaign_info: Dict[str, Any]
    ) -> str:
        """Generate appropriate voicemail message based on campaign"""
        try:
            # Get lead and campaign information
            # This would be customized based on the campaign
            
            template = f"""Hi, this is an automated message from {campaign_info.get('company_name', 'our company')}. 
            
We're reaching out regarding {campaign_info.get('offer_description', 'an important opportunity')} that may be of interest to you.

Please call us back at {campaign_info.get('callback_number', 'our office')} when you have a moment, or visit our website for more information.

Thank you and have a great day!"""

            return template
            
        except Exception as e:
            logger.error(f"Error generating voicemail template: {e}")
            return "Thank you for your time. Please call us back when convenient."
    
    async def end_detection(self, call_log_id: int) -> Dict[str, Any]:
        """End voicemail detection and return summary"""
        try:
            if call_log_id in self.active_detections:
                detection = self.active_detections[call_log_id]
                
                summary = {
                    'call_log_id': call_log_id,
                    'final_state': detection['state'].value,
                    'total_duration': detection['total_duration'],
                    'audio_segments_analyzed': len(detection['audio_segments']),
                    'human_indicators': detection['human_indicators'],
                    'voicemail_indicators': detection['voicemail_indicators'],
                    'keywords_found': detection['keyword_matches']
                }
                
                # Clean up
                del self.active_detections[call_log_id]
                
                logger.info(f"Ended voicemail detection for call {call_log_id}")
                return summary
            
            return {'error': 'Detection not found'}
            
        except Exception as e:
            logger.error(f"Error ending detection: {e}")
            return {'error': str(e)}


# Global instance
voicemail_detection_service = VoicemailDetectionService() 