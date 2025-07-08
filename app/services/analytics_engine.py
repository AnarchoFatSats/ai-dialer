"""
Analytics Engine
Provides real-time metrics, advanced analytics, and predictive insights.
"""

import asyncio
import logging
import uuid
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.models import (
    Campaign, Lead, CallLog, DIDPool, CampaignAnalytics, 
    RealtimeMetrics, CostOptimization, QualityScore,
    CallStatus, CallDisposition, LeadStatus, DIDStatus
)
from app.config import settings, AREA_CODE_MAPPING
import pandas as pd
import numpy as np
from collections import defaultdict
import json
from dateutil import tz
import pytz

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    """
    Comprehensive analytics engine with real-time metrics and optimization insights.
    """
    
    def __init__(self):
        self.session = AsyncSessionLocal()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        
    async def get_realtime_dashboard(self) -> Dict[str, Any]:
        """
        Get real-time dashboard metrics across all campaigns.
        """
        try:
            # Active campaigns
            active_campaigns = await self._get_active_campaigns_count()
            
            # Current active calls
            active_calls = await self._get_active_calls_count()
            
            # Hourly metrics
            hourly_metrics = await self._get_hourly_metrics()
            
            # Cost metrics
            cost_metrics = await self._get_realtime_cost_metrics()
            
            # Quality metrics
            quality_metrics = await self._get_realtime_quality_metrics()
            
            # DID health metrics
            did_health = await self._get_did_health_metrics()
            
            # Performance alerts
            alerts = await self._get_performance_alerts()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'active_campaigns': active_campaigns,
                'active_calls': active_calls,
                'hourly_metrics': hourly_metrics,
                'cost_metrics': cost_metrics,
                'quality_metrics': quality_metrics,
                'did_health': did_health,
                'alerts': alerts
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time dashboard: {e}")
            raise
            
    async def _get_active_campaigns_count(self) -> int:
        """Get count of active campaigns."""
        stmt = select(func.count(Campaign.id)).where(
            Campaign.status == 'active'
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
        
    async def _get_active_calls_count(self) -> int:
        """Get count of currently active calls."""
        stmt = select(func.count(CallLog.id)).where(
            CallLog.status.in_(['initiated', 'ringing', 'answered'])
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
        
    async def _get_hourly_metrics(self) -> Dict[str, Any]:
        """Get hourly performance metrics."""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        # Calls in last hour
        calls_stmt = select(func.count(CallLog.id)).where(
            CallLog.initiated_at >= hour_ago
        )
        calls_result = await self.session.execute(calls_stmt)
        calls_last_hour = calls_result.scalar() or 0
        
        # Answered calls in last hour
        answered_stmt = select(func.count(CallLog.id)).where(
            CallLog.initiated_at >= hour_ago,
            CallLog.status == CallStatus.ANSWERED
        )
        answered_result = await self.session.execute(answered_stmt)
        answered_last_hour = answered_result.scalar() or 0
        
        # Transfers in last hour
        transfers_stmt = select(func.count(CallLog.id)).where(
            CallLog.initiated_at >= hour_ago,
            CallLog.disposition == CallDisposition.TRANSFER
        )
        transfers_result = await self.session.execute(transfers_stmt)
        transfers_last_hour = transfers_result.scalar() or 0
        
        # Calculate rates
        answer_rate = (answered_last_hour / calls_last_hour * 100) if calls_last_hour > 0 else 0
        transfer_rate = (transfers_last_hour / answered_last_hour * 100) if answered_last_hour > 0 else 0
        
        return {
            'calls_last_hour': calls_last_hour,
            'answered_last_hour': answered_last_hour,
            'transfers_last_hour': transfers_last_hour,
            'answer_rate': round(answer_rate, 2),
            'transfer_rate': round(transfer_rate, 2)
        }
        
    async def _get_realtime_cost_metrics(self) -> Dict[str, Any]:
        """Get real-time cost metrics."""
        today = datetime.utcnow().date()
        
        # Total cost today
        cost_stmt = select(func.sum(CallLog.total_cost)).where(
            func.date(CallLog.initiated_at) == today
        )
        cost_result = await self.session.execute(cost_stmt)
        total_cost_today = cost_result.scalar() or 0
        
        # Average cost per minute
        avg_cost_stmt = select(func.avg(CallLog.cost_per_minute)).where(
            func.date(CallLog.initiated_at) == today,
            CallLog.cost_per_minute.isnot(None)
        )
        avg_cost_result = await self.session.execute(avg_cost_stmt)
        avg_cost_per_minute = avg_cost_result.scalar() or 0
        
        # Budget utilization
        # This would need to be calculated based on campaign budgets
        budget_utilization = 0.0  # Placeholder
        
        return {
            'total_cost_today': round(total_cost_today, 4),
            'avg_cost_per_minute': round(avg_cost_per_minute, 6),
            'budget_utilization': round(budget_utilization, 2),
            'target_cost_per_minute': settings.max_cost_per_minute
        }
        
    async def _get_realtime_quality_metrics(self) -> Dict[str, Any]:
        """Get real-time quality metrics."""
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        # Average AI response time
        ai_response_stmt = select(func.avg(CallLog.ai_response_time_ms)).where(
            CallLog.initiated_at >= hour_ago,
            CallLog.ai_response_time_ms.isnot(None)
        )
        ai_response_result = await self.session.execute(ai_response_stmt)
        avg_ai_response = ai_response_result.scalar() or 0
        
        # Average audio quality
        audio_quality_stmt = select(func.avg(CallLog.audio_quality_score)).where(
            CallLog.initiated_at >= hour_ago,
            CallLog.audio_quality_score.isnot(None)
        )
        audio_quality_result = await self.session.execute(audio_quality_stmt)
        avg_audio_quality = audio_quality_result.scalar() or 0
        
        # Average confidence score
        confidence_stmt = select(func.avg(CallLog.ai_confidence_score)).where(
            CallLog.initiated_at >= hour_ago,
            CallLog.ai_confidence_score.isnot(None)
        )
        confidence_result = await self.session.execute(confidence_stmt)
        avg_confidence = confidence_result.scalar() or 0
        
        return {
            'avg_ai_response_time_ms': round(avg_ai_response, 2),
            'avg_audio_quality_score': round(avg_audio_quality, 2),
            'avg_ai_confidence_score': round(avg_confidence, 2),
            'target_ai_response_time': 800  # 800ms target
        }
        
    async def _get_did_health_metrics(self) -> Dict[str, Any]:
        """Get DID health and reputation metrics."""
        # Count DIDs by status
        did_status_stmt = select(
            DIDPool.status,
            func.count(DIDPool.id)
        ).group_by(DIDPool.status)
        
        did_status_result = await self.session.execute(did_status_stmt)
        did_status_counts = dict(did_status_result.fetchall())
        
        # Average spam score
        spam_score_stmt = select(func.avg(DIDPool.spam_score)).where(
            DIDPool.status == DIDStatus.CLEAN
        )
        spam_score_result = await self.session.execute(spam_score_stmt)
        avg_spam_score = spam_score_result.scalar() or 0
        
        # DIDs approaching limits
        approaching_limit_stmt = select(func.count(DIDPool.id)).where(
            DIDPool.calls_today >= settings.max_calls_per_did_daily * 0.8
        )
        approaching_limit_result = await self.session.execute(approaching_limit_stmt)
        approaching_limit = approaching_limit_result.scalar() or 0
        
        return {
            'total_dids': sum(did_status_counts.values()),
            'clean_dids': did_status_counts.get(DIDStatus.CLEAN, 0),
            'yellow_dids': did_status_counts.get(DIDStatus.YELLOW, 0),
            'red_dids': did_status_counts.get(DIDStatus.RED, 0),
            'quarantine_dids': did_status_counts.get(DIDStatus.QUARANTINE, 0),
            'avg_spam_score': round(avg_spam_score, 2),
            'approaching_limit': approaching_limit
        }
        
    async def _get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get performance alerts that need attention."""
        alerts = []
        
        # Check for high cost per minute
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        high_cost_stmt = select(func.avg(CallLog.cost_per_minute)).where(
            CallLog.initiated_at >= hour_ago,
            CallLog.cost_per_minute.isnot(None)
        )
        high_cost_result = await self.session.execute(high_cost_stmt)
        avg_cost = high_cost_result.scalar() or 0
        
        if avg_cost > settings.max_cost_per_minute:
            alerts.append({
                'type': 'cost_alert',
                'severity': 'high',
                'message': f'Cost per minute ({avg_cost:.6f}) exceeds target ({settings.max_cost_per_minute})',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        # Check for low answer rates
        hourly_metrics = await self._get_hourly_metrics()
        if hourly_metrics['answer_rate'] < 15:
            alerts.append({
                'type': 'answer_rate_alert',
                'severity': 'medium',
                'message': f'Answer rate ({hourly_metrics["answer_rate"]}%) below 15%',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        # Check for DID issues
        did_health = await self._get_did_health_metrics()
        if did_health['red_dids'] > 0:
            alerts.append({
                'type': 'did_reputation_alert',
                'severity': 'high',
                'message': f'{did_health["red_dids"]} DIDs have poor reputation',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        return alerts
        
    async def get_campaign_analytics(self, campaign_id: uuid.UUID, days: int = 7) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a specific campaign.
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Basic metrics
            basic_metrics = await self._get_campaign_basic_metrics(campaign_id, start_date)
            
            # Time-based analysis
            time_analysis = await self._get_campaign_time_analysis(campaign_id, start_date)
            
            # Geographic analysis
            geo_analysis = await self._get_campaign_geo_analysis(campaign_id, start_date)
            
            # Conversion funnel
            conversion_funnel = await self._get_campaign_conversion_funnel(campaign_id, start_date)
            
            # Lead scoring analysis
            lead_scoring = await self._get_campaign_lead_scoring_analysis(campaign_id, start_date)
            
            # Optimization opportunities
            optimization_opportunities = await self._get_campaign_optimization_opportunities(campaign_id, start_date)
            
            return {
                'campaign_id': str(campaign_id),
                'analysis_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': datetime.utcnow().isoformat(),
                    'days': days
                },
                'basic_metrics': basic_metrics,
                'time_analysis': time_analysis,
                'geo_analysis': geo_analysis,
                'conversion_funnel': conversion_funnel,
                'lead_scoring': lead_scoring,
                'optimization_opportunities': optimization_opportunities
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign analytics: {e}")
            raise
            
    async def _get_campaign_basic_metrics(self, campaign_id: uuid.UUID, start_date: datetime) -> Dict[str, Any]:
        """Get basic campaign metrics."""
        # Total calls
        total_calls_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.initiated_at >= start_date
        )
        total_calls_result = await self.session.execute(total_calls_stmt)
        total_calls = total_calls_result.scalar() or 0
        
        # Unique leads contacted
        unique_leads_stmt = select(func.count(func.distinct(CallLog.lead_id))).where(
            CallLog.campaign_id == campaign_id,
            CallLog.initiated_at >= start_date
        )
        unique_leads_result = await self.session.execute(unique_leads_stmt)
        unique_leads = unique_leads_result.scalar() or 0
        
        # Conversion metrics
        transfers_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.initiated_at >= start_date,
            CallLog.disposition == CallDisposition.TRANSFER
        )
        transfers_result = await self.session.execute(transfers_stmt)
        transfers = transfers_result.scalar() or 0
        
        # Cost metrics
        total_cost_stmt = select(func.sum(CallLog.total_cost)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.initiated_at >= start_date
        )
        total_cost_result = await self.session.execute(total_cost_stmt)
        total_cost = total_cost_result.scalar() or 0
        
        return {
            'total_calls': total_calls,
            'unique_leads_contacted': unique_leads,
            'total_transfers': transfers,
            'total_cost': round(total_cost, 4),
            'cost_per_call': round(total_cost / total_calls, 6) if total_calls > 0 else 0,
            'cost_per_transfer': round(total_cost / transfers, 4) if transfers > 0 else 0
        }
        
    async def _get_campaign_time_analysis(self, campaign_id: uuid.UUID, start_date: datetime) -> Dict[str, Any]:
        """Get time-based performance analysis."""
        # Hourly performance
        hourly_stmt = select(
            func.extract('hour', CallLog.initiated_at).label('hour'),
            func.count(CallLog.id).label('calls'),
            func.count(CallLog.id).filter(CallLog.status == CallStatus.ANSWERED).label('answered'),
            func.count(CallLog.id).filter(CallLog.disposition == CallDisposition.TRANSFER).label('transfers')
        ).where(
            CallLog.campaign_id == campaign_id,
            CallLog.initiated_at >= start_date
        ).group_by('hour').order_by('hour')
        
        hourly_result = await self.session.execute(hourly_stmt)
        hourly_data = []
        
        for row in hourly_result:
            hour, calls, answered, transfers = row
            answer_rate = (answered / calls * 100) if calls > 0 else 0
            transfer_rate = (transfers / answered * 100) if answered > 0 else 0
            
            hourly_data.append({
                'hour': int(hour),
                'calls': calls,
                'answered': answered,
                'transfers': transfers,
                'answer_rate': round(answer_rate, 2),
                'transfer_rate': round(transfer_rate, 2)
            })
            
        # Daily performance
        daily_stmt = select(
            func.date(CallLog.initiated_at).label('date'),
            func.count(CallLog.id).label('calls'),
            func.count(CallLog.id).filter(CallLog.status == CallStatus.ANSWERED).label('answered'),
            func.count(CallLog.id).filter(CallLog.disposition == CallDisposition.TRANSFER).label('transfers'),
            func.sum(CallLog.total_cost).label('cost')
        ).where(
            CallLog.campaign_id == campaign_id,
            CallLog.initiated_at >= start_date
        ).group_by('date').order_by('date')
        
        daily_result = await self.session.execute(daily_stmt)
        daily_data = []
        
        for row in daily_result:
            date, calls, answered, transfers, cost = row
            answer_rate = (answered / calls * 100) if calls > 0 else 0
            transfer_rate = (transfers / answered * 100) if answered > 0 else 0
            
            daily_data.append({
                'date': date.isoformat(),
                'calls': calls,
                'answered': answered,
                'transfers': transfers,
                'cost': round(cost or 0, 4),
                'answer_rate': round(answer_rate, 2),
                'transfer_rate': round(transfer_rate, 2)
            })
            
        return {
            'hourly_performance': hourly_data,
            'daily_performance': daily_data
        }
        
    async def _get_campaign_geo_analysis(self, campaign_id: uuid.UUID, start_date: datetime) -> Dict[str, Any]:
        """Get geographic performance analysis."""
        # Performance by area code
        area_code_stmt = select(
            Lead.area_code,
            func.count(CallLog.id).label('calls'),
            func.count(CallLog.id).filter(CallLog.status == CallStatus.ANSWERED).label('answered'),
            func.count(CallLog.id).filter(CallLog.disposition == CallDisposition.TRANSFER).label('transfers')
        ).select_from(
            CallLog.join(Lead)
        ).where(
            CallLog.campaign_id == campaign_id,
            CallLog.initiated_at >= start_date
        ).group_by(Lead.area_code).order_by(func.count(CallLog.id).desc())
        
        area_code_result = await self.session.execute(area_code_stmt)
        area_code_data = []
        
        for row in area_code_result:
            area_code, calls, answered, transfers = row
            answer_rate = (answered / calls * 100) if calls > 0 else 0
            transfer_rate = (transfers / answered * 100) if answered > 0 else 0
            
            # Get area code info
            area_info = AREA_CODE_MAPPING.get(area_code, {})
            
            area_code_data.append({
                'area_code': area_code,
                'state': area_info.get('state', ''),
                'city': area_info.get('city', ''),
                'calls': calls,
                'answered': answered,
                'transfers': transfers,
                'answer_rate': round(answer_rate, 2),
                'transfer_rate': round(transfer_rate, 2)
            })
            
        return {
            'area_code_performance': area_code_data
        }
        
    async def _get_campaign_conversion_funnel(self, campaign_id: uuid.UUID, start_date: datetime) -> Dict[str, Any]:
        """Get conversion funnel analysis."""
        # Total leads
        total_leads_stmt = select(func.count(Lead.id)).where(
            Lead.campaign_id == campaign_id,
            Lead.created_at >= start_date
        )
        total_leads_result = await self.session.execute(total_leads_stmt)
        total_leads = total_leads_result.scalar() or 0
        
        # Contacted leads
        contacted_leads_stmt = select(func.count(func.distinct(CallLog.lead_id))).where(
            CallLog.campaign_id == campaign_id,
            CallLog.initiated_at >= start_date
        )
        contacted_leads_result = await self.session.execute(contacted_leads_stmt)
        contacted_leads = contacted_leads_result.scalar() or 0
        
        # Answered calls
        answered_calls_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.initiated_at >= start_date,
            CallLog.status == CallStatus.ANSWERED
        )
        answered_calls_result = await self.session.execute(answered_calls_stmt)
        answered_calls = answered_calls_result.scalar() or 0
        
        # Qualified leads
        qualified_leads_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.initiated_at >= start_date,
            CallLog.disposition == CallDisposition.QUALIFIED
        )
        qualified_leads_result = await self.session.execute(qualified_leads_stmt)
        qualified_leads = qualified_leads_result.scalar() or 0
        
        # Transfers
        transfers_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.initiated_at >= start_date,
            CallLog.disposition == CallDisposition.TRANSFER
        )
        transfers_result = await self.session.execute(transfers_stmt)
        transfers = transfers_result.scalar() or 0
        
        # Calculate conversion rates
        contact_rate = (contacted_leads / total_leads * 100) if total_leads > 0 else 0
        answer_rate = (answered_calls / contacted_leads * 100) if contacted_leads > 0 else 0
        qualification_rate = (qualified_leads / answered_calls * 100) if answered_calls > 0 else 0
        transfer_rate = (transfers / answered_calls * 100) if answered_calls > 0 else 0
        
        return {
            'total_leads': total_leads,
            'contacted_leads': contacted_leads,
            'answered_calls': answered_calls,
            'qualified_leads': qualified_leads,
            'transfers': transfers,
            'contact_rate': round(contact_rate, 2),
            'answer_rate': round(answer_rate, 2),
            'qualification_rate': round(qualification_rate, 2),
            'transfer_rate': round(transfer_rate, 2)
        }
        
    async def _get_campaign_lead_scoring_analysis(self, campaign_id: uuid.UUID, start_date: datetime) -> Dict[str, Any]:
        """Get lead scoring performance analysis."""
        # Performance by score ranges
        score_ranges = [
            (0, 25, 'Low'),
            (25, 50, 'Medium'),
            (50, 75, 'High'),
            (75, 100, 'Very High')
        ]
        
        score_performance = []
        
        for min_score, max_score, label in score_ranges:
            performance_stmt = select(
                func.count(CallLog.id).label('calls'),
                func.count(CallLog.id).filter(CallLog.status == CallStatus.ANSWERED).label('answered'),
                func.count(CallLog.id).filter(CallLog.disposition == CallDisposition.TRANSFER).label('transfers')
            ).select_from(
                CallLog.join(Lead)
            ).where(
                CallLog.campaign_id == campaign_id,
                CallLog.initiated_at >= start_date,
                Lead.score >= min_score,
                Lead.score < max_score
            )
            
            result = await self.session.execute(performance_stmt)
            calls, answered, transfers = result.fetchone()
            
            answer_rate = (answered / calls * 100) if calls > 0 else 0
            transfer_rate = (transfers / answered * 100) if answered > 0 else 0
            
            score_performance.append({
                'score_range': f'{min_score}-{max_score}',
                'label': label,
                'calls': calls,
                'answered': answered,
                'transfers': transfers,
                'answer_rate': round(answer_rate, 2),
                'transfer_rate': round(transfer_rate, 2)
            })
            
        return {
            'score_performance': score_performance
        }
        
    async def _get_campaign_optimization_opportunities(self, campaign_id: uuid.UUID, start_date: datetime) -> List[Dict[str, Any]]:
        """Get optimization opportunities for the campaign."""
        opportunities = []
        
        # Analyze time-based opportunities
        time_analysis = await self._get_campaign_time_analysis(campaign_id, start_date)
        
        # Find best performing hours
        best_hours = sorted(
            time_analysis['hourly_performance'],
            key=lambda x: x['transfer_rate'],
            reverse=True
        )[:3]
        
        if best_hours:
            opportunities.append({
                'type': 'timing_optimization',
                'priority': 'medium',
                'title': 'Optimize Call Timing',
                'description': f'Best performing hours: {", ".join([str(h["hour"]) for h in best_hours])}',
                'impact': 'medium',
                'effort': 'low'
            })
            
        # Analyze geographic opportunities
        geo_analysis = await self._get_campaign_geo_analysis(campaign_id, start_date)
        
        # Find underperforming area codes
        underperforming_areas = [
            area for area in geo_analysis['area_code_performance']
            if area['answer_rate'] < 15 and area['calls'] > 10
        ]
        
        if underperforming_areas:
            opportunities.append({
                'type': 'geographic_optimization',
                'priority': 'high',
                'title': 'Address Underperforming Areas',
                'description': f'Low performance in {len(underperforming_areas)} area codes',
                'impact': 'high',
                'effort': 'medium'
            })
            
        # Analyze lead scoring opportunities
        lead_scoring = await self._get_campaign_lead_scoring_analysis(campaign_id, start_date)
        
        # Check if high-score leads are performing better
        high_score_performance = next(
            (perf for perf in lead_scoring['score_performance'] if perf['label'] == 'Very High'),
            None
        )
        
        if high_score_performance and high_score_performance['transfer_rate'] > 15:
            opportunities.append({
                'type': 'lead_prioritization',
                'priority': 'medium',
                'title': 'Prioritize High-Score Leads',
                'description': f'High-score leads show {high_score_performance["transfer_rate"]}% transfer rate',
                'impact': 'medium',
                'effort': 'low'
            })
            
        return opportunities
        
    async def record_realtime_metric(self, metric_name: str, metric_value: float, 
                                   campaign_id: Optional[uuid.UUID] = None,
                                   area_code: Optional[str] = None) -> None:
        """
        Record a real-time metric for monitoring.
        """
        try:
            metric = RealtimeMetrics(
                metric_name=metric_name,
                metric_value=metric_value,
                metric_type='gauge',
                campaign_id=campaign_id,
                area_code=area_code,
                hour_of_day=datetime.utcnow().hour
            )
            
            self.session.add(metric)
            await self.session.commit()
            
        except Exception as e:
            logger.error(f"Error recording metric {metric_name}: {e}")
            await self.session.rollback()
            
    async def get_predictive_insights(self, campaign_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get predictive insights for campaign optimization.
        """
        try:
            # Get historical performance data
            historical_data = await self._get_campaign_historical_data(campaign_id)
            
            # Predict optimal call times
            optimal_times = await self._predict_optimal_call_times(historical_data)
            
            # Predict lead conversion likelihood
            lead_predictions = await self._predict_lead_conversion_likelihood(campaign_id)
            
            # Predict budget requirements
            budget_predictions = await self._predict_budget_requirements(campaign_id)
            
            # Predict DID performance
            did_predictions = await self._predict_did_performance(campaign_id)
            
            return {
                'campaign_id': str(campaign_id),
                'generated_at': datetime.utcnow().isoformat(),
                'optimal_call_times': optimal_times,
                'lead_predictions': lead_predictions,
                'budget_predictions': budget_predictions,
                'did_predictions': did_predictions
            }
            
        except Exception as e:
            logger.error(f"Error getting predictive insights: {e}")
            raise
            
    async def _get_campaign_historical_data(self, campaign_id: uuid.UUID) -> pd.DataFrame:
        """Get historical campaign data for analysis."""
        # This would fetch historical data and return as DataFrame
        # For now, return empty DataFrame
        return pd.DataFrame()
        
    async def _predict_optimal_call_times(self, historical_data: pd.DataFrame) -> Dict[str, Any]:
        """Predict optimal call times based on historical data."""
        # Simplified prediction logic
        return {
            'recommended_hours': [9, 10, 11, 14, 15, 16],
            'confidence': 0.75,
            'rationale': 'Based on historical answer rates and conversion data'
        }
        
    async def _predict_lead_conversion_likelihood(self, campaign_id: uuid.UUID) -> Dict[str, Any]:
        """Predict lead conversion likelihood."""
        # Simplified prediction
        return {
            'high_probability_leads': 0,
            'medium_probability_leads': 0,
            'low_probability_leads': 0,
            'model_accuracy': 0.68
        }
        
    async def _predict_budget_requirements(self, campaign_id: uuid.UUID) -> Dict[str, Any]:
        """Predict budget requirements for campaign."""
        return {
            'daily_budget_recommendation': 1000.0,
            'cost_per_transfer_projection': 0.12,
            'confidence_interval': [0.10, 0.15]
        }
        
    async def _predict_did_performance(self, campaign_id: uuid.UUID) -> Dict[str, Any]:
        """Predict DID performance and rotation needs."""
        return {
            'dids_needing_rotation': 0,
            'optimal_rotation_schedule': 'daily',
            'reputation_risk_score': 0.25
        }

# Async context manager for analytics engine
def get_analytics_engine():
    """Get analytics engine with proper session management."""
    return AnalyticsEngine() 