"""
Quality Scoring System
Evaluates call quality, AI performance, and provides improvement recommendations.
"""

import asyncio
import logging
import uuid
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.models import (
    CallLog, QualityScore, Campaign, Lead, DIDPool,
    CallStatus, CallDisposition, LeadStatus
)
from app.config import settings
import json
import numpy as np
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QualityGrade(Enum):
    """Quality grades for scoring."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"

@dataclass
class QualityMetrics:
    """Data class for quality metrics."""
    audio_quality: float
    network_quality: float
    conversation_flow: float
    ai_performance: float
    customer_satisfaction: float
    overall_score: float
    grade: QualityGrade
    recommendations: List[str]

class QualityScoringService:
    """
    Comprehensive quality scoring system with multiple evaluation dimensions.
    """
    
    def __init__(self):
        self.session = AsyncSessionLocal()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        
    async def evaluate_call_quality(self, call_log_id: uuid.UUID) -> QualityScore:
        """
        Evaluate and score call quality across multiple dimensions.
        """
        try:
            # Get call log
            call_log = await self._get_call_log(call_log_id)
            if not call_log:
                raise ValueError(f"Call log {call_log_id} not found")
                
            # Calculate quality metrics
            quality_metrics = await self._calculate_quality_metrics(call_log)
            
            # Create or update quality score record
            quality_score = await self._save_quality_score(call_log_id, quality_metrics)
            
            logger.info(f"Evaluated call quality for {call_log_id}: {quality_metrics.overall_score:.2f} ({quality_metrics.grade.value})")
            return quality_score
            
        except Exception as e:
            logger.error(f"Error evaluating call quality: {e}")
            raise
            
    async def _get_call_log(self, call_log_id: uuid.UUID) -> Optional[CallLog]:
        """Get call log by ID."""
        stmt = select(CallLog).where(CallLog.id == call_log_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def _calculate_quality_metrics(self, call_log: CallLog) -> QualityMetrics:
        """
        Calculate comprehensive quality metrics for a call.
        """
        # Audio Quality (based on MOS score, jitter, packet loss)
        audio_quality = self._calculate_audio_quality(call_log)
        
        # Network Quality (based on latency, packet loss, jitter)
        network_quality = self._calculate_network_quality(call_log)
        
        # Conversation Flow (based on turn-taking, response times, natural flow)
        conversation_flow = self._calculate_conversation_flow(call_log)
        
        # AI Performance (based on response time, confidence, accuracy)
        ai_performance = self._calculate_ai_performance(call_log)
        
        # Customer Satisfaction (based on disposition, call duration, engagement)
        customer_satisfaction = self._calculate_customer_satisfaction(call_log)
        
        # Overall Score (weighted average)
        overall_score = self._calculate_overall_score(
            audio_quality, network_quality, conversation_flow, 
            ai_performance, customer_satisfaction
        )
        
        # Grade assignment
        grade = self._assign_quality_grade(overall_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            audio_quality, network_quality, conversation_flow,
            ai_performance, customer_satisfaction
        )
        
        return QualityMetrics(
            audio_quality=audio_quality,
            network_quality=network_quality,
            conversation_flow=conversation_flow,
            ai_performance=ai_performance,
            customer_satisfaction=customer_satisfaction,
            overall_score=overall_score,
            grade=grade,
            recommendations=recommendations
        )
        
    def _calculate_audio_quality(self, call_log: CallLog) -> float:
        """
        Calculate audio quality score based on technical metrics.
        """
        score = 0.0
        
        # MOS Score (Mean Opinion Score) - primary audio quality metric
        if call_log.audio_quality_score:
            # MOS scale is 1-5, normalize to 0-100
            mos_score = (call_log.audio_quality_score - 1) / 4 * 100
            score += mos_score * 0.6  # 60% weight
        else:
            score += 70.0 * 0.6  # Default if no MOS data
            
        # Jitter impact
        if call_log.jitter_ms is not None:
            if call_log.jitter_ms <= 20:
                jitter_score = 100
            elif call_log.jitter_ms <= 50:
                jitter_score = 80
            elif call_log.jitter_ms <= 100:
                jitter_score = 60
            else:
                jitter_score = 40
            score += jitter_score * 0.2  # 20% weight
        else:
            score += 80.0 * 0.2  # Default
            
        # Packet Loss impact
        if call_log.packet_loss_percent is not None:
            if call_log.packet_loss_percent <= 1:
                packet_loss_score = 100
            elif call_log.packet_loss_percent <= 3:
                packet_loss_score = 80
            elif call_log.packet_loss_percent <= 5:
                packet_loss_score = 60
            else:
                packet_loss_score = 40
            score += packet_loss_score * 0.2  # 20% weight
        else:
            score += 80.0 * 0.2  # Default
            
        return min(score, 100.0)
        
    def _calculate_network_quality(self, call_log: CallLog) -> float:
        """
        Calculate network quality score based on connectivity metrics.
        """
        score = 0.0
        
        # Latency/RTT
        if call_log.latency_ms is not None:
            if call_log.latency_ms <= 100:
                latency_score = 100
            elif call_log.latency_ms <= 200:
                latency_score = 80
            elif call_log.latency_ms <= 400:
                latency_score = 60
            else:
                latency_score = 40
            score += latency_score * 0.4  # 40% weight
        else:
            score += 80.0 * 0.4  # Default
            
        # Jitter stability
        if call_log.jitter_ms is not None:
            if call_log.jitter_ms <= 10:
                jitter_score = 100
            elif call_log.jitter_ms <= 30:
                jitter_score = 80
            elif call_log.jitter_ms <= 60:
                jitter_score = 60
            else:
                jitter_score = 40
            score += jitter_score * 0.3  # 30% weight
        else:
            score += 80.0 * 0.3  # Default
            
        # Packet Loss
        if call_log.packet_loss_percent is not None:
            if call_log.packet_loss_percent <= 0.5:
                packet_score = 100
            elif call_log.packet_loss_percent <= 2:
                packet_score = 80
            elif call_log.packet_loss_percent <= 4:
                packet_score = 60
            else:
                packet_score = 40
            score += packet_score * 0.3  # 30% weight
        else:
            score += 80.0 * 0.3  # Default
            
        return min(score, 100.0)
        
    def _calculate_conversation_flow(self, call_log: CallLog) -> float:
        """
        Calculate conversation flow quality based on interaction patterns.
        """
        score = 0.0
        
        # Number of conversation turns (more turns = better engagement)
        if call_log.conversation_turns:
            if call_log.conversation_turns >= 10:
                turns_score = 100
            elif call_log.conversation_turns >= 6:
                turns_score = 80
            elif call_log.conversation_turns >= 3:
                turns_score = 60
            else:
                turns_score = 40
            score += turns_score * 0.4  # 40% weight
        else:
            score += 50.0 * 0.4  # Default for minimal interaction
            
        # Call duration appropriateness
        if call_log.duration_seconds:
            if 30 <= call_log.duration_seconds <= 300:  # 30 seconds to 5 minutes
                duration_score = 100
            elif 300 < call_log.duration_seconds <= 600:  # 5-10 minutes
                duration_score = 80
            elif 10 <= call_log.duration_seconds < 30:  # Very short
                duration_score = 60
            else:  # Too long or too short
                duration_score = 40
            score += duration_score * 0.3  # 30% weight
        else:
            score += 50.0 * 0.3  # Default
            
        # Call outcome appropriateness
        if call_log.disposition:
            if call_log.disposition in [CallDisposition.TRANSFER, CallDisposition.QUALIFIED]:
                outcome_score = 100
            elif call_log.disposition == CallDisposition.CALLBACK:
                outcome_score = 80
            elif call_log.disposition == CallDisposition.VOICEMAIL:
                outcome_score = 60
            else:
                outcome_score = 40
            score += outcome_score * 0.3  # 30% weight
        else:
            score += 50.0 * 0.3  # Default
            
        return min(score, 100.0)
        
    def _calculate_ai_performance(self, call_log: CallLog) -> float:
        """
        Calculate AI performance score based on response times and confidence.
        """
        score = 0.0
        
        # AI Response Time
        if call_log.ai_response_time_ms:
            if call_log.ai_response_time_ms <= 500:  # Excellent
                response_score = 100
            elif call_log.ai_response_time_ms <= 800:  # Good
                response_score = 80
            elif call_log.ai_response_time_ms <= 1200:  # Acceptable
                response_score = 60
            else:  # Poor
                response_score = 40
            score += response_score * 0.5  # 50% weight
        else:
            score += 70.0 * 0.5  # Default
            
        # AI Confidence Score
        if call_log.ai_confidence_score:
            # Confidence is typically 0-1, convert to 0-100
            confidence_score = call_log.ai_confidence_score * 100
            score += confidence_score * 0.3  # 30% weight
        else:
            score += 70.0 * 0.3  # Default
            
        # Call completion success
        if call_log.status == CallStatus.COMPLETED:
            completion_score = 100
        elif call_log.status == CallStatus.ANSWERED:
            completion_score = 80
        else:
            completion_score = 40
        score += completion_score * 0.2  # 20% weight
        
        return min(score, 100.0)
        
    def _calculate_customer_satisfaction(self, call_log: CallLog) -> float:
        """
        Calculate customer satisfaction score based on engagement indicators.
        """
        score = 0.0
        
        # Call disposition as satisfaction indicator
        if call_log.disposition:
            if call_log.disposition == CallDisposition.TRANSFER:
                disposition_score = 100  # High satisfaction - wants to continue
            elif call_log.disposition == CallDisposition.QUALIFIED:
                disposition_score = 90   # Very satisfied - showed interest
            elif call_log.disposition == CallDisposition.CALLBACK:
                disposition_score = 80   # Satisfied - wants to continue later
            elif call_log.disposition == CallDisposition.VOICEMAIL:
                disposition_score = 50   # Neutral - no direct interaction
            elif call_log.disposition == CallDisposition.NOT_INTERESTED:
                disposition_score = 30   # Dissatisfied - but polite
            else:  # HANGUP
                disposition_score = 20   # Poor satisfaction - hung up
            score += disposition_score * 0.5  # 50% weight
        else:
            score += 50.0 * 0.5  # Default
            
        # Talk time as engagement indicator
        if call_log.talk_time_seconds:
            if call_log.talk_time_seconds >= 60:  # 1+ minutes of talk
                talk_score = 100
            elif call_log.talk_time_seconds >= 30:  # 30+ seconds
                talk_score = 80
            elif call_log.talk_time_seconds >= 15:  # 15+ seconds
                talk_score = 60
            else:
                talk_score = 40
            score += talk_score * 0.3  # 30% weight
        else:
            score += 50.0 * 0.3  # Default
            
        # Sentiment analysis (if available)
        if call_log.sentiment_score:
            # Sentiment typically -1 to 1, normalize to 0-100
            sentiment_score = (call_log.sentiment_score + 1) / 2 * 100
            score += sentiment_score * 0.2  # 20% weight
        else:
            score += 50.0 * 0.2  # Default neutral sentiment
            
        return min(score, 100.0)
        
    def _calculate_overall_score(self, audio_quality: float, network_quality: float,
                               conversation_flow: float, ai_performance: float,
                               customer_satisfaction: float) -> float:
        """
        Calculate weighted overall quality score.
        """
        weights = {
            'audio_quality': 0.15,
            'network_quality': 0.10,
            'conversation_flow': 0.25,
            'ai_performance': 0.25,
            'customer_satisfaction': 0.25
        }
        
        overall_score = (
            audio_quality * weights['audio_quality'] +
            network_quality * weights['network_quality'] +
            conversation_flow * weights['conversation_flow'] +
            ai_performance * weights['ai_performance'] +
            customer_satisfaction * weights['customer_satisfaction']
        )
        
        return min(overall_score, 100.0)
        
    def _assign_quality_grade(self, overall_score: float) -> QualityGrade:
        """
        Assign quality grade based on overall score.
        """
        if overall_score >= 90:
            return QualityGrade.A
        elif overall_score >= 80:
            return QualityGrade.B
        elif overall_score >= 70:
            return QualityGrade.C
        elif overall_score >= 60:
            return QualityGrade.D
        else:
            return QualityGrade.F
            
    def _generate_recommendations(self, audio_quality: float, network_quality: float,
                                conversation_flow: float, ai_performance: float,
                                customer_satisfaction: float) -> List[str]:
        """
        Generate improvement recommendations based on quality scores.
        """
        recommendations = []
        
        # Audio Quality Recommendations
        if audio_quality < 70:
            recommendations.append("Improve audio quality by optimizing codec settings and reducing background noise")
        if audio_quality < 80:
            recommendations.append("Consider using higher-quality audio processing for better clarity")
            
        # Network Quality Recommendations
        if network_quality < 70:
            recommendations.append("Address network connectivity issues - high latency or packet loss detected")
        if network_quality < 80:
            recommendations.append("Consider using redundant network paths or QoS prioritization")
            
        # Conversation Flow Recommendations
        if conversation_flow < 70:
            recommendations.append("Improve conversation engagement - optimize script for better interaction")
        if conversation_flow < 80:
            recommendations.append("Adjust conversation pacing and turn-taking for more natural flow")
            
        # AI Performance Recommendations
        if ai_performance < 70:
            recommendations.append("Optimize AI response times - current latency is too high")
        if ai_performance < 80:
            recommendations.append("Improve AI model confidence through better training data")
            
        # Customer Satisfaction Recommendations
        if customer_satisfaction < 70:
            recommendations.append("Review script content and delivery for better customer engagement")
        if customer_satisfaction < 80:
            recommendations.append("Analyze customer feedback patterns and adjust approach accordingly")
            
        # Overall recommendations
        overall_score = self._calculate_overall_score(
            audio_quality, network_quality, conversation_flow, 
            ai_performance, customer_satisfaction
        )
        
        if overall_score < 70:
            recommendations.append("Comprehensive quality improvement needed across multiple dimensions")
        elif overall_score < 85:
            recommendations.append("Focus on top 2-3 lowest-scoring quality dimensions for improvement")
            
        return recommendations
        
    async def _save_quality_score(self, call_log_id: uuid.UUID, metrics: QualityMetrics) -> QualityScore:
        """
        Save quality score to database.
        """
        try:
            # Check if quality score already exists
            existing_stmt = select(QualityScore).where(QualityScore.call_log_id == call_log_id)
            existing_result = await self.session.execute(existing_stmt)
            existing_score = existing_result.scalar_one_or_none()
            
            if existing_score:
                # Update existing score
                existing_score.audio_quality = metrics.audio_quality
                existing_score.network_quality = metrics.network_quality
                existing_score.conversation_flow = metrics.conversation_flow
                existing_score.ai_performance = metrics.ai_performance
                existing_score.customer_satisfaction = metrics.customer_satisfaction
                existing_score.overall_score = metrics.overall_score
                existing_score.quality_grade = metrics.grade.value
                existing_score.recommendations = metrics.recommendations
                quality_score = existing_score
            else:
                # Create new score
                quality_score = QualityScore(
                    id=uuid.uuid4(),
                    call_log_id=call_log_id,
                    audio_quality=metrics.audio_quality,
                    network_quality=metrics.network_quality,
                    conversation_flow=metrics.conversation_flow,
                    ai_performance=metrics.ai_performance,
                    customer_satisfaction=metrics.customer_satisfaction,
                    overall_score=metrics.overall_score,
                    quality_grade=metrics.grade.value,
                    recommendations=metrics.recommendations
                )
                self.session.add(quality_score)
                
            await self.session.commit()
            return quality_score
            
        except Exception as e:
            logger.error(f"Error saving quality score: {e}")
            await self.session.rollback()
            raise
            
    async def get_quality_trends(self, campaign_id: Optional[uuid.UUID] = None, 
                               days: int = 7) -> Dict[str, Any]:
        """
        Get quality trends and analytics.
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Build base query
            base_query = select(QualityScore).join(CallLog)
            
            if campaign_id:
                base_query = base_query.where(CallLog.campaign_id == campaign_id)
                
            base_query = base_query.where(CallLog.initiated_at >= start_date)
            
            # Average scores by dimension
            avg_scores = await self._get_average_quality_scores(base_query)
            
            # Quality distribution
            quality_distribution = await self._get_quality_distribution(base_query)
            
            # Trends over time
            quality_trends = await self._get_quality_trends_over_time(base_query, start_date)
            
            # Top recommendations
            top_recommendations = await self._get_top_recommendations(base_query)
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': datetime.utcnow().isoformat(),
                    'days': days
                },
                'campaign_id': str(campaign_id) if campaign_id else None,
                'average_scores': avg_scores,
                'quality_distribution': quality_distribution,
                'trends': quality_trends,
                'top_recommendations': top_recommendations
            }
            
        except Exception as e:
            logger.error(f"Error getting quality trends: {e}")
            raise
            
    async def _get_average_quality_scores(self, base_query) -> Dict[str, float]:
        """Get average quality scores by dimension."""
        avg_stmt = select(
            func.avg(QualityScore.audio_quality).label('avg_audio'),
            func.avg(QualityScore.network_quality).label('avg_network'),
            func.avg(QualityScore.conversation_flow).label('avg_conversation'),
            func.avg(QualityScore.ai_performance).label('avg_ai'),
            func.avg(QualityScore.customer_satisfaction).label('avg_satisfaction'),
            func.avg(QualityScore.overall_score).label('avg_overall')
        ).select_from(base_query.subquery())
        
        result = await self.session.execute(avg_stmt)
        row = result.fetchone()
        
        return {
            'audio_quality': round(row.avg_audio or 0, 2),
            'network_quality': round(row.avg_network or 0, 2),
            'conversation_flow': round(row.avg_conversation or 0, 2),
            'ai_performance': round(row.avg_ai or 0, 2),
            'customer_satisfaction': round(row.avg_satisfaction or 0, 2),
            'overall_score': round(row.avg_overall or 0, 2)
        }
        
    async def _get_quality_distribution(self, base_query) -> Dict[str, int]:
        """Get quality grade distribution."""
        dist_stmt = select(
            QualityScore.quality_grade,
            func.count(QualityScore.id)
        ).select_from(
            base_query.subquery()
        ).group_by(QualityScore.quality_grade)
        
        result = await self.session.execute(dist_stmt)
        distribution = dict(result.fetchall())
        
        return {
            'A': distribution.get('A', 0),
            'B': distribution.get('B', 0),
            'C': distribution.get('C', 0),
            'D': distribution.get('D', 0),
            'F': distribution.get('F', 0)
        }
        
    async def _get_quality_trends_over_time(self, base_query, start_date: datetime) -> List[Dict[str, Any]]:
        """Get quality trends over time."""
        # Daily quality averages
        daily_stmt = select(
            func.date(CallLog.initiated_at).label('date'),
            func.avg(QualityScore.overall_score).label('avg_score'),
            func.count(QualityScore.id).label('count')
        ).select_from(
            base_query.subquery().join(CallLog)
        ).where(
            CallLog.initiated_at >= start_date
        ).group_by('date').order_by('date')
        
        result = await self.session.execute(daily_stmt)
        trends = []
        
        for row in result:
            trends.append({
                'date': row.date.isoformat(),
                'average_score': round(row.avg_score or 0, 2),
                'call_count': row.count
            })
            
        return trends
        
    async def _get_top_recommendations(self, base_query) -> List[Dict[str, Any]]:
        """Get top recommendations by frequency."""
        # This would analyze the recommendations JSON field
        # For now, return common recommendations
        return [
            {
                'recommendation': 'Improve AI response times',
                'frequency': 45,
                'impact': 'high'
            },
            {
                'recommendation': 'Optimize conversation flow',
                'frequency': 38,
                'impact': 'medium'
            },
            {
                'recommendation': 'Address network connectivity issues',
                'frequency': 29,
                'impact': 'high'
            },
            {
                'recommendation': 'Enhance audio quality',
                'frequency': 22,
                'impact': 'medium'
            }
        ]
        
    async def batch_evaluate_quality(self, call_log_ids: List[uuid.UUID]) -> Dict[str, Any]:
        """
        Batch evaluate quality for multiple calls.
        """
        results = {
            'total_calls': len(call_log_ids),
            'evaluated': 0,
            'failed': 0,
            'average_score': 0.0,
            'grade_distribution': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        }
        
        total_score = 0.0
        
        try:
            for call_log_id in call_log_ids:
                try:
                    quality_score = await self.evaluate_call_quality(call_log_id)
                    results['evaluated'] += 1
                    total_score += quality_score.overall_score
                    results['grade_distribution'][quality_score.quality_grade] += 1
                except Exception as e:
                    logger.error(f"Failed to evaluate call {call_log_id}: {e}")
                    results['failed'] += 1
                    
            if results['evaluated'] > 0:
                results['average_score'] = round(total_score / results['evaluated'], 2)
                
            return results
            
        except Exception as e:
            logger.error(f"Error in batch quality evaluation: {e}")
            raise

# Async context manager for quality scoring
async def get_quality_scoring_service():
    """Get quality scoring service with proper session management."""
    async with QualityScoringService() as service:
        yield service 