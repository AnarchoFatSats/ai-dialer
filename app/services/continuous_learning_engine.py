import logging
import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import statistics
from sqlalchemy import select, func, and_, or_, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import (
    Campaign, CallLog, CallStatus, CallDisposition, Lead, 
    CampaignAnalytics, CampaignStatus
)
from app.services.claude_service import claude_service

logger = logging.getLogger(__name__)


class LearningTrigger(Enum):
    CALL_COMPLETED = "call_completed"
    DAILY_ANALYSIS = "daily_analysis"
    PERFORMANCE_THRESHOLD = "performance_threshold"
    MANUAL_TRIGGER = "manual_trigger"


@dataclass
class PerformanceMetrics:
    """Campaign performance metrics for learning analysis"""
    campaign_id: str
    total_calls: int
    answered_calls: int
    qualified_leads: int
    successful_transfers: int
    failed_transfers: int
    average_call_duration: float
    average_objections: float
    sentiment_scores: List[float]
    success_rate: float
    time_period: str


@dataclass
class LearningInsight:
    """Insights derived from performance analysis"""
    insight_id: str
    campaign_id: str
    insight_type: str  # "objection_handling", "timing", "approach", "voice_optimization"
    confidence_score: float
    description: str
    recommendation: str
    data_points: int
    impact_estimate: float
    implementation_priority: str  # "high", "medium", "low"
    supporting_evidence: Dict[str, Any]
    created_at: datetime


@dataclass
class OptimizationAction:
    """Actions to improve performance based on insights"""
    action_id: str
    campaign_id: str
    action_type: str
    description: str
    implementation_data: Dict[str, Any]
    expected_impact: float
    status: str  # "pending", "applied", "testing", "proven"
    created_at: datetime
    applied_at: Optional[datetime] = None


class ContinuousLearningEngine:
    """
    Analyzes call outcomes and continuously improves AI performance.
    
    This engine:
    1. Monitors call success/failure patterns
    2. Identifies optimization opportunities
    3. Automatically adjusts AI behavior
    4. Tracks performance improvements
    5. Learns from transfer success rates
    """
    
    def __init__(self):
        self.learning_queue: List[str] = []  # Campaign IDs to analyze
        self.optimization_history: Dict[str, List[OptimizationAction]] = defaultdict(list)
        self.performance_cache: Dict[str, PerformanceMetrics] = {}
        self.learning_enabled = True
        
    async def start_learning_engine(self):
        """Start the continuous learning background process"""
        logger.info("Starting continuous learning engine")
        
        # Run learning cycles
        while self.learning_enabled:
            try:
                # Process learning queue
                await self._process_learning_queue()
                
                # Daily analysis for all active campaigns
                await self._run_daily_analysis()
                
                # Check performance thresholds
                await self._check_performance_thresholds()
                
                # Wait before next cycle
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in learning engine cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def trigger_learning(self, campaign_id: str, trigger: LearningTrigger):
        """Trigger learning analysis for a specific campaign"""
        logger.info(f"Learning triggered for campaign {campaign_id}: {trigger.value}")
        
        if campaign_id not in self.learning_queue:
            self.learning_queue.append(campaign_id)
    
    async def analyze_call_outcome(self, call_log_id: str):
        """Analyze a single call outcome for learning"""
        
        async with AsyncSessionLocal() as session:
            try:
                # Get call details
                call_query = select(CallLog).where(CallLog.id == call_log_id)
                result = await session.execute(call_query)
                call_log = result.scalar_one_or_none()
                
                if not call_log:
                    return
                
                # Trigger learning for this campaign
                await self.trigger_learning(str(call_log.campaign_id), LearningTrigger.CALL_COMPLETED)
                
                # Immediate analysis for high-impact calls
                if call_log.disposition == CallDisposition.TRANSFER:
                    await self._analyze_successful_transfer(call_log, session)
                elif call_log.disposition in [CallDisposition.HANGUP, CallDisposition.NOT_INTERESTED]:
                    await self._analyze_failed_call(call_log, session)
                    
            except Exception as e:
                logger.error(f"Error analyzing call outcome: {e}")
    
    async def _process_learning_queue(self):
        """Process campaigns in the learning queue"""
        
        while self.learning_queue:
            campaign_id = self.learning_queue.pop(0)
            await self._analyze_campaign_performance(campaign_id)
    
    async def _analyze_campaign_performance(self, campaign_id: str):
        """Comprehensive analysis of campaign performance"""
        
        async with AsyncSessionLocal() as session:
            try:
                # Get performance metrics
                metrics = await self._get_performance_metrics(campaign_id, session)
                
                if not metrics or metrics.total_calls < 10:
                    logger.info(f"Insufficient data for campaign {campaign_id}")
                    return
                
                # Generate insights
                insights = await self._generate_learning_insights(metrics, session)
                
                # Create optimization actions
                actions = await self._create_optimization_actions(insights, session)
                
                # Apply high-priority optimizations
                await self._apply_optimizations(actions, session)
                
                # Update performance cache
                self.performance_cache[campaign_id] = metrics
                
                logger.info(f"Learning analysis completed for campaign {campaign_id}: {len(insights)} insights, {len(actions)} actions")
                
            except Exception as e:
                logger.error(f"Error analyzing campaign {campaign_id}: {e}")
    
    async def _get_performance_metrics(self, campaign_id: str, session: AsyncSession) -> Optional[PerformanceMetrics]:
        """Get comprehensive performance metrics for a campaign"""
        
        try:
            # Time window - last 7 days
            start_date = datetime.utcnow() - timedelta(days=7)
            
            # Basic call metrics
            call_stats = await session.execute(
                select(
                    func.count(CallLog.id).label('total_calls'),
                    func.sum(func.case((CallLog.status == CallStatus.ANSWERED, 1), else_=0)).label('answered'),
                    func.sum(func.case((CallLog.disposition == CallDisposition.QUALIFIED, 1), else_=0)).label('qualified'),
                    func.sum(func.case((CallLog.disposition == CallDisposition.TRANSFER, 1), else_=0)).label('transfers'),
                    func.sum(func.case((CallLog.transfer_attempted == True, CallLog.transfer_successful == False, 1), else_=0)).label('failed_transfers'),
                    func.avg(CallLog.duration_seconds).label('avg_duration'),
                    func.avg(CallLog.objections_count).label('avg_objections')
                ).where(
                    CallLog.campaign_id == campaign_id,
                    CallLog.initiated_at >= start_date
                )
            )
            
            stats = call_stats.first()
            
            if not stats or stats.total_calls == 0:
                return None
            
            # Sentiment scores
            sentiment_query = await session.execute(
                select(CallLog.sentiment_score).where(
                    CallLog.campaign_id == campaign_id,
                    CallLog.initiated_at >= start_date,
                    CallLog.sentiment_score.isnot(None)
                )
            )
            sentiment_scores = [score[0] for score in sentiment_query.fetchall() if score[0] is not None]
            
            # Calculate success rate
            success_rate = (stats.transfers / stats.answered * 100) if stats.answered > 0 else 0
            
            return PerformanceMetrics(
                campaign_id=campaign_id,
                total_calls=stats.total_calls,
                answered_calls=stats.answered or 0,
                qualified_leads=stats.qualified or 0,
                successful_transfers=stats.transfers or 0,
                failed_transfers=stats.failed_transfers or 0,
                average_call_duration=stats.avg_duration or 0,
                average_objections=stats.avg_objections or 0,
                sentiment_scores=sentiment_scores,
                success_rate=success_rate,
                time_period="7_days"
            )
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return None
    
    async def _generate_learning_insights(self, metrics: PerformanceMetrics, session: AsyncSession) -> List[LearningInsight]:
        """Generate learning insights from performance data"""
        
        insights = []
        
        # Analyze transfer success patterns
        transfer_insights = await self._analyze_transfer_patterns(metrics, session)
        insights.extend(transfer_insights)
        
        # Analyze objection handling
        objection_insights = await self._analyze_objection_patterns(metrics, session)
        insights.extend(objection_insights)
        
        # Analyze timing patterns
        timing_insights = await self._analyze_timing_patterns(metrics, session)
        insights.extend(timing_insights)
        
        # Analyze conversation flow
        flow_insights = await self._analyze_conversation_flow(metrics, session)
        insights.extend(flow_insights)
        
        # Analyze sentiment patterns
        sentiment_insights = await self._analyze_sentiment_patterns(metrics, session)
        insights.extend(sentiment_insights)
        
        return insights
    
    async def _analyze_transfer_patterns(self, metrics: PerformanceMetrics, session: AsyncSession) -> List[LearningInsight]:
        """Analyze what leads to successful vs failed transfers"""
        
        insights = []
        
        try:
            # Compare successful vs failed transfers
            transfer_analysis = await session.execute(
                select(
                    CallLog.transfer_successful,
                    func.avg(CallLog.duration_seconds).label('avg_duration'),
                    func.avg(CallLog.objections_count).label('avg_objections'),
                    func.avg(CallLog.sentiment_score).label('avg_sentiment'),
                    func.count(CallLog.id).label('count')
                ).where(
                    CallLog.campaign_id == metrics.campaign_id,
                    CallLog.transfer_attempted == True,
                    CallLog.initiated_at >= datetime.utcnow() - timedelta(days=7)
                ).group_by(CallLog.transfer_successful)
            )
            
            transfer_data = {row.transfer_successful: row for row in transfer_analysis}
            
            if True in transfer_data and False in transfer_data:
                successful = transfer_data[True]
                failed = transfer_data[False]
                
                # Duration pattern
                if successful.avg_duration and failed.avg_duration:
                    duration_diff = successful.avg_duration - failed.avg_duration
                    if abs(duration_diff) > 30:  # 30 seconds difference
                        insight = LearningInsight(
                            insight_id=str(uuid.uuid4()),
                            campaign_id=metrics.campaign_id,
                            insight_type="timing",
                            confidence_score=0.8,
                            description=f"Successful transfers have {'longer' if duration_diff > 0 else 'shorter'} conversations by {abs(duration_diff):.0f} seconds",
                            recommendation=f"Optimize conversation length to {successful.avg_duration:.0f} seconds for better transfer success",
                            data_points=successful.count + failed.count,
                            impact_estimate=0.15,  # 15% improvement estimate
                            implementation_priority="high",
                            supporting_evidence={
                                "successful_avg_duration": successful.avg_duration,
                                "failed_avg_duration": failed.avg_duration,
                                "successful_count": successful.count,
                                "failed_count": failed.count
                            },
                            created_at=datetime.utcnow()
                        )
                        insights.append(insight)
                
                # Objection pattern
                if successful.avg_objections and failed.avg_objections:
                    objection_diff = failed.avg_objections - successful.avg_objections
                    if objection_diff > 0.5:  # Significant difference
                        insight = LearningInsight(
                            insight_id=str(uuid.uuid4()),
                            campaign_id=metrics.campaign_id,
                            insight_type="objection_handling",
                            confidence_score=0.9,
                            description=f"Failed transfers have {objection_diff:.1f} more objections on average",
                            recommendation="Improve objection handling to reduce objections before transfer",
                            data_points=successful.count + failed.count,
                            impact_estimate=0.2,  # 20% improvement estimate
                            implementation_priority="high",
                            supporting_evidence={
                                "successful_avg_objections": successful.avg_objections,
                                "failed_avg_objections": failed.avg_objections
                            },
                            created_at=datetime.utcnow()
                        )
                        insights.append(insight)
            
        except Exception as e:
            logger.error(f"Error analyzing transfer patterns: {e}")
        
        return insights
    
    async def _analyze_objection_patterns(self, metrics: PerformanceMetrics, session: AsyncSession) -> List[LearningInsight]:
        """Analyze objection handling effectiveness"""
        
        insights = []
        
        try:
            # Analyze objection count vs success rate
            objection_analysis = await session.execute(
                select(
                    CallLog.objections_count,
                    func.count(CallLog.id).label('total_calls'),
                    func.sum(func.case((CallLog.disposition == CallDisposition.TRANSFER, 1), else_=0)).label('transfers')
                ).where(
                    CallLog.campaign_id == metrics.campaign_id,
                    CallLog.initiated_at >= datetime.utcnow() - timedelta(days=7)
                ).group_by(CallLog.objections_count)
            )
            
            objection_data = []
            for row in objection_analysis:
                if row.total_calls > 0:
                    success_rate = row.transfers / row.total_calls * 100
                    objection_data.append({
                        'objections': row.objections_count,
                        'success_rate': success_rate,
                        'total_calls': row.total_calls
                    })
            
            if len(objection_data) >= 2:
                # Find optimal objection count
                optimal = max(objection_data, key=lambda x: x['success_rate'])
                
                if optimal['objections'] > 0:
                    insight = LearningInsight(
                        insight_id=str(uuid.uuid4()),
                        campaign_id=metrics.campaign_id,
                        insight_type="objection_handling",
                        confidence_score=0.7,
                        description=f"Calls with {optimal['objections']} objections have the highest success rate ({optimal['success_rate']:.1f}%)",
                        recommendation=f"Optimize objection handling to achieve {optimal['objections']} objections per call",
                        data_points=sum(d['total_calls'] for d in objection_data),
                        impact_estimate=0.12,
                        implementation_priority="medium",
                        supporting_evidence={'objection_analysis': objection_data},
                        created_at=datetime.utcnow()
                    )
                    insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error analyzing objection patterns: {e}")
        
        return insights
    
    async def _analyze_timing_patterns(self, metrics: PerformanceMetrics, session: AsyncSession) -> List[LearningInsight]:
        """Analyze optimal timing patterns"""
        
        insights = []
        
        try:
            # Hour of day analysis
            hourly_analysis = await session.execute(
                select(
                    func.extract('hour', CallLog.initiated_at).label('hour'),
                    func.count(CallLog.id).label('total_calls'),
                    func.sum(func.case((CallLog.status == CallStatus.ANSWERED, 1), else_=0)).label('answered'),
                    func.sum(func.case((CallLog.disposition == CallDisposition.TRANSFER, 1), else_=0)).label('transfers')
                ).where(
                    CallLog.campaign_id == metrics.campaign_id,
                    CallLog.initiated_at >= datetime.utcnow() - timedelta(days=7)
                ).group_by('hour')
            )
            
            hourly_data = []
            for row in hourly_analysis:
                answer_rate = (row.answered / row.total_calls * 100) if row.total_calls > 0 else 0
                success_rate = (row.transfers / row.answered * 100) if row.answered > 0 else 0
                
                hourly_data.append({
                    'hour': int(row.hour),
                    'answer_rate': answer_rate,
                    'success_rate': success_rate,
                    'total_calls': row.total_calls
                })
            
            if len(hourly_data) >= 3:
                # Find best performing hours
                best_hours = sorted(hourly_data, key=lambda x: x['success_rate'], reverse=True)[:3]
                
                if best_hours[0]['success_rate'] > metrics.success_rate * 1.2:  # 20% better
                    insight = LearningInsight(
                        insight_id=str(uuid.uuid4()),
                        campaign_id=metrics.campaign_id,
                        insight_type="timing",
                        confidence_score=0.8,
                        description=f"Calls at {best_hours[0]['hour']}:00 have {best_hours[0]['success_rate']:.1f}% success rate",
                        recommendation=f"Focus calling efforts on hours: {', '.join([f'{h['hour']}:00' for h in best_hours])}",
                        data_points=sum(d['total_calls'] for d in hourly_data),
                        impact_estimate=0.18,
                        implementation_priority="high",
                        supporting_evidence={'hourly_data': hourly_data},
                        created_at=datetime.utcnow()
                    )
                    insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error analyzing timing patterns: {e}")
        
        return insights
    
    async def _analyze_conversation_flow(self, metrics: PerformanceMetrics, session: AsyncSession) -> List[LearningInsight]:
        """Analyze conversation flow effectiveness"""
        
        insights = []
        
        try:
            # Analyze conversation turns vs success
            turns_analysis = await session.execute(
                select(
                    CallLog.conversation_turns,
                    func.count(CallLog.id).label('total_calls'),
                    func.sum(func.case((CallLog.disposition == CallDisposition.TRANSFER, 1), else_=0)).label('transfers')
                ).where(
                    CallLog.campaign_id == metrics.campaign_id,
                    CallLog.initiated_at >= datetime.utcnow() - timedelta(days=7),
                    CallLog.conversation_turns.isnot(None)
                ).group_by(CallLog.conversation_turns)
            )
            
            turns_data = []
            for row in turns_analysis:
                if row.total_calls > 0:
                    success_rate = row.transfers / row.total_calls * 100
                    turns_data.append({
                        'turns': row.conversation_turns,
                        'success_rate': success_rate,
                        'total_calls': row.total_calls
                    })
            
            if len(turns_data) >= 3:
                # Find optimal conversation length
                optimal = max(turns_data, key=lambda x: x['success_rate'])
                
                insight = LearningInsight(
                    insight_id=str(uuid.uuid4()),
                    campaign_id=metrics.campaign_id,
                    insight_type="approach",
                    confidence_score=0.6,
                    description=f"Conversations with {optimal['turns']} turns have the highest success rate ({optimal['success_rate']:.1f}%)",
                    recommendation=f"Optimize conversation flow to achieve {optimal['turns']} conversational turns",
                    data_points=sum(d['total_calls'] for d in turns_data),
                    impact_estimate=0.1,
                    implementation_priority="medium",
                    supporting_evidence={'turns_analysis': turns_data},
                    created_at=datetime.utcnow()
                )
                insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error analyzing conversation flow: {e}")
        
        return insights
    
    async def _analyze_sentiment_patterns(self, metrics: PerformanceMetrics, session: AsyncSession) -> List[LearningInsight]:
        """Analyze sentiment score patterns"""
        
        insights = []
        
        try:
            if not metrics.sentiment_scores:
                return insights
            
            # Analyze sentiment vs success
            sentiment_analysis = await session.execute(
                select(
                    CallLog.sentiment_score,
                    CallLog.disposition
                ).where(
                    CallLog.campaign_id == metrics.campaign_id,
                    CallLog.initiated_at >= datetime.utcnow() - timedelta(days=7),
                    CallLog.sentiment_score.isnot(None)
                )
            )
            
            successful_sentiments = []
            failed_sentiments = []
            
            for row in sentiment_analysis:
                if row.disposition == CallDisposition.TRANSFER:
                    successful_sentiments.append(row.sentiment_score)
                elif row.disposition in [CallDisposition.HANGUP, CallDisposition.NOT_INTERESTED]:
                    failed_sentiments.append(row.sentiment_score)
            
            if len(successful_sentiments) >= 5 and len(failed_sentiments) >= 5:
                avg_successful = statistics.mean(successful_sentiments)
                avg_failed = statistics.mean(failed_sentiments)
                
                if avg_successful - avg_failed > 0.2:  # Significant difference
                    insight = LearningInsight(
                        insight_id=str(uuid.uuid4()),
                        campaign_id=metrics.campaign_id,
                        insight_type="approach",
                        confidence_score=0.7,
                        description=f"Successful transfers have {avg_successful:.2f} avg sentiment vs {avg_failed:.2f} for failed calls",
                        recommendation="Focus on improving conversation sentiment and rapport building",
                        data_points=len(successful_sentiments) + len(failed_sentiments),
                        impact_estimate=0.15,
                        implementation_priority="high",
                        supporting_evidence={
                            'successful_sentiment_avg': avg_successful,
                            'failed_sentiment_avg': avg_failed,
                            'successful_count': len(successful_sentiments),
                            'failed_count': len(failed_sentiments)
                        },
                        created_at=datetime.utcnow()
                    )
                    insights.append(insight)
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment patterns: {e}")
        
        return insights
    
    async def _create_optimization_actions(self, insights: List[LearningInsight], session: AsyncSession) -> List[OptimizationAction]:
        """Create optimization actions based on insights"""
        
        actions = []
        
        for insight in insights:
            action = OptimizationAction(
                action_id=str(uuid.uuid4()),
                campaign_id=insight.campaign_id,
                action_type=insight.insight_type,
                description=insight.recommendation,
                implementation_data=await self._create_implementation_data(insight),
                expected_impact=insight.impact_estimate,
                status="pending",
                created_at=datetime.utcnow()
            )
            actions.append(action)
        
        return actions
    
    async def _create_implementation_data(self, insight: LearningInsight) -> Dict[str, Any]:
        """Create implementation data for optimization actions"""
        
        if insight.insight_type == "objection_handling":
            return {
                "type": "prompt_optimization",
                "target": "objection_handling_prompt",
                "optimization": "improve_objection_responses",
                "data": insight.supporting_evidence
            }
        elif insight.insight_type == "timing":
            return {
                "type": "schedule_optimization",
                "target": "calling_schedule",
                "optimization": "focus_on_optimal_hours",
                "data": insight.supporting_evidence
            }
        elif insight.insight_type == "approach":
            return {
                "type": "conversation_optimization",
                "target": "conversation_flow",
                "optimization": "adjust_conversation_length",
                "data": insight.supporting_evidence
            }
        else:
            return {"type": "general", "data": insight.supporting_evidence}
    
    async def _apply_optimizations(self, actions: List[OptimizationAction], session: AsyncSession):
        """Apply high-priority optimizations automatically"""
        
        for action in actions:
            if action.implementation_data.get("type") == "prompt_optimization":
                await self._apply_prompt_optimization(action, session)
            elif action.implementation_data.get("type") == "schedule_optimization":
                await self._apply_schedule_optimization(action, session)
            elif action.implementation_data.get("type") == "conversation_optimization":
                await self._apply_conversation_optimization(action, session)
    
    async def _apply_prompt_optimization(self, action: OptimizationAction, session: AsyncSession):
        """Apply prompt optimization based on learning"""
        
        try:
            # Get current campaign
            campaign_query = select(Campaign).where(Campaign.id == action.campaign_id)
            result = await session.execute(campaign_query)
            campaign = result.scalar_one_or_none()
            
            if not campaign:
                return
            
            # Use Claude to improve objection handling
            current_prompt = campaign.objection_handling_prompt
            improvement_context = action.implementation_data.get("data", {})
            
            improved_prompt = await claude_service.generate_content(
                f"""Improve this objection handling prompt based on performance data:

Current prompt: {current_prompt}

Performance insights: {json.dumps(improvement_context, indent=2)}

Create an improved version that:
1. Addresses the specific patterns found in the data
2. Maintains the same tone and style
3. Focuses on reducing objections and improving success rates
4. Keeps responses under 50 words per objection

Return only the improved prompt text."""
            )
            
            # Update campaign with improved prompt
            await session.execute(
                update(Campaign)
                .where(Campaign.id == action.campaign_id)
                .values(objection_handling_prompt=improved_prompt)
            )
            
            # Mark action as applied
            action.status = "applied"
            action.applied_at = datetime.utcnow()
            
            # Store in optimization history
            self.optimization_history[action.campaign_id].append(action)
            
            logger.info(f"Applied prompt optimization for campaign {action.campaign_id}")
            
        except Exception as e:
            logger.error(f"Error applying prompt optimization: {e}")
    
    async def _apply_schedule_optimization(self, action: OptimizationAction, session: AsyncSession):
        """Apply schedule optimization based on timing insights"""
        
        try:
            # This would integrate with campaign scheduling
            # For now, just log the optimization
            logger.info(f"Schedule optimization recommended for campaign {action.campaign_id}: {action.description}")
            
            action.status = "applied"
            action.applied_at = datetime.utcnow()
            self.optimization_history[action.campaign_id].append(action)
            
        except Exception as e:
            logger.error(f"Error applying schedule optimization: {e}")
    
    async def _apply_conversation_optimization(self, action: OptimizationAction, session: AsyncSession):
        """Apply conversation flow optimization"""
        
        try:
            # This would update conversation flow parameters
            logger.info(f"Conversation optimization recommended for campaign {action.campaign_id}: {action.description}")
            
            action.status = "applied"
            action.applied_at = datetime.utcnow()
            self.optimization_history[action.campaign_id].append(action)
            
        except Exception as e:
            logger.error(f"Error applying conversation optimization: {e}")
    
    async def _analyze_successful_transfer(self, call_log: CallLog, session: AsyncSession):
        """Immediate analysis of successful transfers"""
        
        try:
            # Extract successful patterns
            success_pattern = {
                "duration": call_log.duration_seconds,
                "objections": call_log.objections_count,
                "sentiment": call_log.sentiment_score,
                "turns": call_log.conversation_turns,
                "hour": call_log.initiated_at.hour if call_log.initiated_at else None
            }
            
            # Store pattern for learning
            # This could be used to reinforce successful behaviors
            logger.info(f"Successful transfer pattern captured: {success_pattern}")
            
        except Exception as e:
            logger.error(f"Error analyzing successful transfer: {e}")
    
    async def _analyze_failed_call(self, call_log: CallLog, session: AsyncSession):
        """Immediate analysis of failed calls"""
        
        try:
            # Extract failure patterns
            failure_pattern = {
                "duration": call_log.duration_seconds,
                "objections": call_log.objections_count,
                "sentiment": call_log.sentiment_score,
                "turns": call_log.conversation_turns,
                "disposition": call_log.disposition.value if call_log.disposition else None
            }
            
            # Store pattern for learning
            logger.info(f"Failed call pattern captured: {failure_pattern}")
            
        except Exception as e:
            logger.error(f"Error analyzing failed call: {e}")
    
    async def _run_daily_analysis(self):
        """Run daily analysis for all active campaigns"""
        
        try:
            async with AsyncSessionLocal() as session:
                # Get all active campaigns
                campaigns_query = select(Campaign).where(Campaign.status == CampaignStatus.ACTIVE)
                result = await session.execute(campaigns_query)
                campaigns = result.scalars().all()
                
                for campaign in campaigns:
                    await self.trigger_learning(str(campaign.id), LearningTrigger.DAILY_ANALYSIS)
                    
        except Exception as e:
            logger.error(f"Error in daily analysis: {e}")
    
    async def _check_performance_thresholds(self):
        """Check if any campaigns need immediate attention"""
        
        try:
            for campaign_id, metrics in self.performance_cache.items():
                # Check if success rate has dropped significantly
                if metrics.success_rate < 10 and metrics.total_calls > 50:
                    await self.trigger_learning(campaign_id, LearningTrigger.PERFORMANCE_THRESHOLD)
                    logger.warning(f"Performance threshold triggered for campaign {campaign_id}: {metrics.success_rate}% success rate")
                    
        except Exception as e:
            logger.error(f"Error checking performance thresholds: {e}")
    
    async def get_learning_insights(self, campaign_id: str) -> List[LearningInsight]:
        """Get learning insights for a specific campaign"""
        
        # This would retrieve stored insights from database
        # For now, return recent insights from optimization history
        return []
    
    async def get_optimization_history(self, campaign_id: str) -> List[OptimizationAction]:
        """Get optimization history for a campaign"""
        
        return self.optimization_history.get(campaign_id, [])
    
    def stop_learning_engine(self):
        """Stop the learning engine"""
        self.learning_enabled = False
        logger.info("Learning engine stopped")


# Global instance
continuous_learning_engine = ContinuousLearningEngine() 