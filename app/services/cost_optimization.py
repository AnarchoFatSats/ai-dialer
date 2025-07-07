"""
Cost Optimization Engine
Provides real-time cost tracking, budget management, and optimization recommendations.
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
    Campaign, CallLog, CostOptimization, Lead, DIDPool,
    CallStatus, CallDisposition, CampaignStatus, LeadStatus
)
from app.config import settings
import json
import numpy as np
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class CostAlert(Enum):
    """Cost alert types."""
    BUDGET_WARNING = "budget_warning"
    BUDGET_EXCEEDED = "budget_exceeded"
    COST_PER_MINUTE_HIGH = "cost_per_minute_high"
    COST_PER_TRANSFER_HIGH = "cost_per_transfer_high"
    EFFICIENCY_POOR = "efficiency_poor"

@dataclass
class CostMetrics:
    """Data class for cost metrics."""
    total_cost: float
    cost_per_call: float
    cost_per_transfer: float
    cost_per_minute: float
    budget_utilization: float
    projected_daily_cost: float
    efficiency_score: float
    alerts: List[Dict[str, Any]]

class CostOptimizationEngine:
    """
    Comprehensive cost optimization engine with real-time tracking and predictions.
    """
    
    def __init__(self):
        self.session = AsyncSessionLocal()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        
    async def track_realtime_costs(self, campaign_id: uuid.UUID) -> CostMetrics:
        """
        Track real-time costs for a campaign with alerts and optimization suggestions.
        """
        try:
            # Get campaign
            campaign = await self._get_campaign(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
                
            # Calculate current cost metrics
            cost_metrics = await self._calculate_cost_metrics(campaign_id)
            
            # Check for alerts
            alerts = await self._check_cost_alerts(campaign_id, cost_metrics)
            
            # Update cost optimization record
            await self._update_cost_optimization_record(campaign_id, cost_metrics, alerts)
            
            # Auto-pause if necessary
            if self._should_auto_pause(cost_metrics, alerts):
                await self._auto_pause_campaign(campaign_id, alerts)
                
            logger.info(f"Cost tracking for campaign {campaign_id}: ${cost_metrics.total_cost:.4f} total, {cost_metrics.budget_utilization:.1f}% budget used")
            return cost_metrics
            
        except Exception as e:
            logger.error(f"Error tracking costs for campaign {campaign_id}: {e}")
            raise
            
    async def _get_campaign(self, campaign_id: uuid.UUID) -> Optional[Campaign]:
        """Get campaign by ID."""
        stmt = select(Campaign).where(Campaign.id == campaign_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def _calculate_cost_metrics(self, campaign_id: uuid.UUID) -> CostMetrics:
        """
        Calculate comprehensive cost metrics for a campaign.
        """
        today = datetime.utcnow().date()
        
        # Total cost today
        total_cost_stmt = select(func.sum(CallLog.total_cost)).where(
            CallLog.campaign_id == campaign_id,
            func.date(CallLog.initiated_at) == today
        )
        total_cost_result = await self.session.execute(total_cost_stmt)
        total_cost = total_cost_result.scalar() or 0.0
        
        # Total calls today
        total_calls_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id,
            func.date(CallLog.initiated_at) == today
        )
        total_calls_result = await self.session.execute(total_calls_stmt)
        total_calls = total_calls_result.scalar() or 0
        
        # Total transfers today
        transfers_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id,
            func.date(CallLog.initiated_at) == today,
            CallLog.disposition == CallDisposition.TRANSFER
        )
        transfers_result = await self.session.execute(transfers_stmt)
        transfers = transfers_result.scalar() or 0
        
        # Total talk time today (in minutes)
        talk_time_stmt = select(func.sum(CallLog.talk_time_seconds)).where(
            CallLog.campaign_id == campaign_id,
            func.date(CallLog.initiated_at) == today
        )
        talk_time_result = await self.session.execute(talk_time_stmt)
        talk_time_seconds = talk_time_result.scalar() or 0
        talk_time_minutes = talk_time_seconds / 60.0
        
        # Calculate derived metrics
        cost_per_call = total_cost / total_calls if total_calls > 0 else 0
        cost_per_transfer = total_cost / transfers if transfers > 0 else 0
        cost_per_minute = total_cost / talk_time_minutes if talk_time_minutes > 0 else 0
        
        # Budget utilization
        campaign = await self._get_campaign(campaign_id)
        budget_utilization = (total_cost / campaign.max_daily_budget * 100) if campaign and campaign.max_daily_budget > 0 else 0
        
        # Projected daily cost based on current hourly rate
        current_hour = datetime.utcnow().hour
        if current_hour > 0:
            hourly_rate = total_cost / current_hour
            projected_daily_cost = hourly_rate * 24
        else:
            projected_daily_cost = total_cost
            
        # Efficiency score (higher is better)
        efficiency_score = self._calculate_efficiency_score(
            cost_per_transfer, transfers, total_calls, cost_per_minute
        )
        
        return CostMetrics(
            total_cost=total_cost,
            cost_per_call=cost_per_call,
            cost_per_transfer=cost_per_transfer,
            cost_per_minute=cost_per_minute,
            budget_utilization=budget_utilization,
            projected_daily_cost=projected_daily_cost,
            efficiency_score=efficiency_score,
            alerts=[]  # Will be populated by _check_cost_alerts
        )
        
    def _calculate_efficiency_score(self, cost_per_transfer: float, transfers: int, 
                                  total_calls: int, cost_per_minute: float) -> float:
        """
        Calculate cost efficiency score (0-100, higher is better).
        """
        score = 100.0
        
        # Cost per transfer efficiency
        if cost_per_transfer > 0:
            target_cost_per_transfer = 0.14  # Target $0.14 per transfer
            if cost_per_transfer <= target_cost_per_transfer:
                transfer_score = 100
            elif cost_per_transfer <= target_cost_per_transfer * 1.5:
                transfer_score = 80
            elif cost_per_transfer <= target_cost_per_transfer * 2:
                transfer_score = 60
            else:
                transfer_score = 40
            score = score * 0.4 + transfer_score * 0.4  # 40% weight
        else:
            score = score * 0.4 + 50 * 0.4  # Default for no transfers
            
        # Transfer rate efficiency
        transfer_rate = (transfers / total_calls * 100) if total_calls > 0 else 0
        if transfer_rate >= 10:
            rate_score = 100
        elif transfer_rate >= 7:
            rate_score = 80
        elif transfer_rate >= 5:
            rate_score = 60
        else:
            rate_score = 40
        score = score * 0.6 + rate_score * 0.3  # 30% weight
        
        # Cost per minute efficiency
        target_cost_per_minute = settings.max_cost_per_minute
        if cost_per_minute <= target_cost_per_minute:
            minute_score = 100
        elif cost_per_minute <= target_cost_per_minute * 1.2:
            minute_score = 80
        elif cost_per_minute <= target_cost_per_minute * 1.5:
            minute_score = 60
        else:
            minute_score = 40
        score = score * 0.7 + minute_score * 0.3  # 30% weight
        
        return min(score, 100.0)
        
    async def _check_cost_alerts(self, campaign_id: uuid.UUID, metrics: CostMetrics) -> List[Dict[str, Any]]:
        """
        Check for cost-related alerts and warnings.
        """
        alerts = []
        
        # Budget utilization alerts
        if metrics.budget_utilization >= 100:
            alerts.append({
                'type': CostAlert.BUDGET_EXCEEDED.value,
                'severity': 'critical',
                'message': f'Daily budget exceeded: {metrics.budget_utilization:.1f}% used',
                'recommendation': 'Pause campaign immediately or increase budget',
                'auto_action': 'pause_campaign'
            })
        elif metrics.budget_utilization >= settings.cost_alert_threshold * 100:
            alerts.append({
                'type': CostAlert.BUDGET_WARNING.value,
                'severity': 'warning',
                'message': f'Budget warning: {metrics.budget_utilization:.1f}% used',
                'recommendation': 'Monitor closely and consider optimization',
                'auto_action': None
            })
            
        # Cost per minute alerts
        if metrics.cost_per_minute > settings.max_cost_per_minute * 1.2:
            alerts.append({
                'type': CostAlert.COST_PER_MINUTE_HIGH.value,
                'severity': 'high',
                'message': f'Cost per minute too high: ${metrics.cost_per_minute:.6f}',
                'recommendation': 'Optimize call duration and quality',
                'auto_action': None
            })
            
        # Cost per transfer alerts
        target_cost_per_transfer = 0.14
        if metrics.cost_per_transfer > target_cost_per_transfer * 1.5:
            alerts.append({
                'type': CostAlert.COST_PER_TRANSFER_HIGH.value,
                'severity': 'high',
                'message': f'Cost per transfer too high: ${metrics.cost_per_transfer:.4f}',
                'recommendation': 'Improve lead qualification and script effectiveness',
                'auto_action': None
            })
            
        # Efficiency alerts
        if metrics.efficiency_score < 60:
            alerts.append({
                'type': CostAlert.EFFICIENCY_POOR.value,
                'severity': 'medium',
                'message': f'Poor cost efficiency: {metrics.efficiency_score:.1f}/100',
                'recommendation': 'Review campaign strategy and optimization opportunities',
                'auto_action': None
            })
            
        # Projected cost alerts
        campaign = await self._get_campaign(campaign_id)
        if campaign and metrics.projected_daily_cost > campaign.max_daily_budget * 1.1:
            alerts.append({
                'type': CostAlert.BUDGET_WARNING.value,
                'severity': 'warning',
                'message': f'Projected daily cost: ${metrics.projected_daily_cost:.2f}',
                'recommendation': 'Adjust campaign pacing to stay within budget',
                'auto_action': None
            })
            
        return alerts
        
    def _should_auto_pause(self, metrics: CostMetrics, alerts: List[Dict[str, Any]]) -> bool:
        """
        Determine if campaign should be auto-paused based on cost metrics.
        """
        # Check for critical alerts with auto-pause action
        for alert in alerts:
            if alert.get('auto_action') == 'pause_campaign':
                return True
                
        # Auto-pause if budget severely exceeded
        if metrics.budget_utilization >= 110:  # 110% of budget
            return True
            
        return False
        
    async def _auto_pause_campaign(self, campaign_id: uuid.UUID, alerts: List[Dict[str, Any]]):
        """
        Automatically pause campaign due to cost overruns.
        """
        try:
            campaign = await self._get_campaign(campaign_id)
            if campaign and campaign.status == CampaignStatus.ACTIVE:
                campaign.status = CampaignStatus.PAUSED
                await self.session.commit()
                
                # Log the auto-pause action
                alert_messages = [alert['message'] for alert in alerts if alert.get('auto_action') == 'pause_campaign']
                reason = f"Auto-paused due to cost alerts: {'; '.join(alert_messages)}"
                
                logger.warning(f"Auto-paused campaign {campaign_id}: {reason}")
                
                # TODO: Send notification to campaign managers
                
        except Exception as e:
            logger.error(f"Error auto-pausing campaign {campaign_id}: {e}")
            await self.session.rollback()
            
    async def _update_cost_optimization_record(self, campaign_id: uuid.UUID, 
                                             metrics: CostMetrics, alerts: List[Dict[str, Any]]):
        """
        Update or create cost optimization record.
        """
        try:
            today = datetime.utcnow().date()
            
            # Check if record exists for today
            existing_stmt = select(CostOptimization).where(
                CostOptimization.campaign_id == campaign_id,
                func.date(CostOptimization.date) == today
            )
            existing_result = await self.session.execute(existing_stmt)
            existing_record = existing_result.scalar_one_or_none()
            
            campaign = await self._get_campaign(campaign_id)
            
            if existing_record:
                # Update existing record
                existing_record.current_spend = metrics.total_cost
                existing_record.projected_spend = metrics.projected_daily_cost
                existing_record.actual_cost_per_call = metrics.cost_per_call
                existing_record.actual_cost_per_transfer = metrics.cost_per_transfer
                existing_record.recommended_actions = [alert['recommendation'] for alert in alerts]
                existing_record.auto_pause_triggered = any(alert.get('auto_action') == 'pause_campaign' for alert in alerts)
            else:
                # Create new record
                new_record = CostOptimization(
                    id=uuid.uuid4(),
                    campaign_id=campaign_id,
                    daily_budget=campaign.max_daily_budget if campaign else 0,
                    current_spend=metrics.total_cost,
                    projected_spend=metrics.projected_daily_cost,
                    target_cost_per_call=0.017,  # Target cost per call
                    target_cost_per_transfer=0.14,  # Target cost per transfer
                    actual_cost_per_call=metrics.cost_per_call,
                    actual_cost_per_transfer=metrics.cost_per_transfer,
                    recommended_actions=[alert['recommendation'] for alert in alerts],
                    auto_pause_triggered=any(alert.get('auto_action') == 'pause_campaign' for alert in alerts)
                )
                self.session.add(new_record)
                
            await self.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating cost optimization record: {e}")
            await self.session.rollback()
            
    async def get_cost_optimization_report(self, campaign_id: uuid.UUID, 
                                         days: int = 7) -> Dict[str, Any]:
        """
        Generate comprehensive cost optimization report.
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Historical cost trends
            cost_trends = await self._get_cost_trends(campaign_id, start_date)
            
            # Efficiency analysis
            efficiency_analysis = await self._get_efficiency_analysis(campaign_id, start_date)
            
            # Budget analysis
            budget_analysis = await self._get_budget_analysis(campaign_id, start_date)
            
            # Optimization opportunities
            optimization_opportunities = await self._get_optimization_opportunities(campaign_id, start_date)
            
            # Cost predictions
            cost_predictions = await self._get_cost_predictions(campaign_id)
            
            return {
                'campaign_id': str(campaign_id),
                'report_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': datetime.utcnow().isoformat(),
                    'days': days
                },
                'cost_trends': cost_trends,
                'efficiency_analysis': efficiency_analysis,
                'budget_analysis': budget_analysis,
                'optimization_opportunities': optimization_opportunities,
                'cost_predictions': cost_predictions
            }
            
        except Exception as e:
            logger.error(f"Error generating cost optimization report: {e}")
            raise
            
    async def _get_cost_trends(self, campaign_id: uuid.UUID, start_date: datetime) -> Dict[str, Any]:
        """Get cost trends over time."""
        # Daily cost aggregation
        daily_costs_stmt = select(
            func.date(CallLog.initiated_at).label('date'),
            func.sum(CallLog.total_cost).label('total_cost'),
            func.count(CallLog.id).label('total_calls'),
            func.count(CallLog.id).filter(CallLog.disposition == CallDisposition.TRANSFER).label('transfers'),
            func.avg(CallLog.cost_per_minute).label('avg_cost_per_minute')
        ).where(
            CallLog.campaign_id == campaign_id,
            CallLog.initiated_at >= start_date
        ).group_by('date').order_by('date')
        
        daily_costs_result = await self.session.execute(daily_costs_stmt)
        daily_trends = []
        
        for row in daily_costs_result:
            cost_per_call = row.total_cost / row.total_calls if row.total_calls > 0 else 0
            cost_per_transfer = row.total_cost / row.transfers if row.transfers > 0 else 0
            
            daily_trends.append({
                'date': row.date.isoformat(),
                'total_cost': round(row.total_cost or 0, 4),
                'total_calls': row.total_calls,
                'transfers': row.transfers,
                'cost_per_call': round(cost_per_call, 6),
                'cost_per_transfer': round(cost_per_transfer, 4),
                'avg_cost_per_minute': round(row.avg_cost_per_minute or 0, 6)
            })
            
        return {
            'daily_trends': daily_trends,
            'total_cost': sum(day['total_cost'] for day in daily_trends),
            'total_calls': sum(day['total_calls'] for day in daily_trends),
            'total_transfers': sum(day['transfers'] for day in daily_trends)
        }
        
    async def _get_efficiency_analysis(self, campaign_id: uuid.UUID, start_date: datetime) -> Dict[str, Any]:
        """Get efficiency analysis."""
        # Calculate efficiency metrics
        efficiency_stmt = select(
            func.sum(CallLog.total_cost).label('total_cost'),
            func.count(CallLog.id).label('total_calls'),
            func.count(CallLog.id).filter(CallLog.status == CallStatus.ANSWERED).label('answered_calls'),
            func.count(CallLog.id).filter(CallLog.disposition == CallDisposition.TRANSFER).label('transfers'),
            func.sum(CallLog.talk_time_seconds).label('total_talk_time')
        ).where(
            CallLog.campaign_id == campaign_id,
            CallLog.initiated_at >= start_date
        )
        
        efficiency_result = await self.session.execute(efficiency_stmt)
        row = efficiency_result.fetchone()
        
        if row and row.total_calls > 0:
            answer_rate = (row.answered_calls / row.total_calls) * 100
            transfer_rate = (row.transfers / row.answered_calls) * 100 if row.answered_calls > 0 else 0
            cost_per_call = row.total_cost / row.total_calls
            cost_per_transfer = row.total_cost / row.transfers if row.transfers > 0 else 0
            cost_per_minute = row.total_cost / (row.total_talk_time / 60) if row.total_talk_time > 0 else 0
            
            # Efficiency score
            efficiency_score = self._calculate_efficiency_score(
                cost_per_transfer, row.transfers, row.total_calls, cost_per_minute
            )
            
            return {
                'answer_rate': round(answer_rate, 2),
                'transfer_rate': round(transfer_rate, 2),
                'cost_per_call': round(cost_per_call, 6),
                'cost_per_transfer': round(cost_per_transfer, 4),
                'cost_per_minute': round(cost_per_minute, 6),
                'efficiency_score': round(efficiency_score, 1),
                'efficiency_grade': self._get_efficiency_grade(efficiency_score)
            }
        else:
            return {
                'answer_rate': 0,
                'transfer_rate': 0,
                'cost_per_call': 0,
                'cost_per_transfer': 0,
                'cost_per_minute': 0,
                'efficiency_score': 0,
                'efficiency_grade': 'F'
            }
            
    def _get_efficiency_grade(self, efficiency_score: float) -> str:
        """Get efficiency letter grade."""
        if efficiency_score >= 90:
            return 'A'
        elif efficiency_score >= 80:
            return 'B'
        elif efficiency_score >= 70:
            return 'C'
        elif efficiency_score >= 60:
            return 'D'
        else:
            return 'F'
            
    async def _get_budget_analysis(self, campaign_id: uuid.UUID, start_date: datetime) -> Dict[str, Any]:
        """Get budget utilization analysis."""
        campaign = await self._get_campaign(campaign_id)
        if not campaign:
            return {}
            
        # Daily budget utilization
        daily_budget_stmt = select(
            func.date(CallLog.initiated_at).label('date'),
            func.sum(CallLog.total_cost).label('daily_cost')
        ).where(
            CallLog.campaign_id == campaign_id,
            CallLog.initiated_at >= start_date
        ).group_by('date').order_by('date')
        
        daily_budget_result = await self.session.execute(daily_budget_stmt)
        budget_utilization = []
        
        for row in daily_budget_result:
            utilization = (row.daily_cost / campaign.max_daily_budget * 100) if campaign.max_daily_budget > 0 else 0
            budget_utilization.append({
                'date': row.date.isoformat(),
                'daily_cost': round(row.daily_cost or 0, 4),
                'budget_utilization': round(utilization, 2),
                'remaining_budget': round(campaign.max_daily_budget - (row.daily_cost or 0), 4)
            })
            
        # Overall budget metrics
        total_cost = sum(day['daily_cost'] for day in budget_utilization)
        days_analyzed = len(budget_utilization)
        total_budget = campaign.max_daily_budget * days_analyzed
        overall_utilization = (total_cost / total_budget * 100) if total_budget > 0 else 0
        
        return {
            'daily_budget': campaign.max_daily_budget,
            'total_budget_period': total_budget,
            'total_cost_period': round(total_cost, 4),
            'overall_utilization': round(overall_utilization, 2),
            'daily_utilization': budget_utilization,
            'average_daily_cost': round(total_cost / days_analyzed, 4) if days_analyzed > 0 else 0
        }
        
    async def _get_optimization_opportunities(self, campaign_id: uuid.UUID, 
                                           start_date: datetime) -> List[Dict[str, Any]]:
        """Get cost optimization opportunities."""
        opportunities = []
        
        # Get efficiency analysis
        efficiency = await self._get_efficiency_analysis(campaign_id, start_date)
        
        # Cost per transfer optimization
        if efficiency['cost_per_transfer'] > 0.14:
            savings_potential = (efficiency['cost_per_transfer'] - 0.14) * efficiency.get('transfers', 0)
            opportunities.append({
                'type': 'cost_per_transfer',
                'priority': 'high',
                'title': 'Reduce Cost Per Transfer',
                'description': f'Current cost per transfer ${efficiency["cost_per_transfer"]:.4f} vs target $0.14',
                'potential_savings': round(savings_potential, 2),
                'recommended_actions': [
                    'Improve lead qualification',
                    'Optimize script for better conversion',
                    'Review call timing strategy'
                ]
            })
            
        # Answer rate optimization
        if efficiency['answer_rate'] < 20:
            opportunities.append({
                'type': 'answer_rate',
                'priority': 'high',
                'title': 'Improve Answer Rate',
                'description': f'Current answer rate {efficiency["answer_rate"]:.1f}% is below optimal',
                'potential_savings': 'Reduce cost per contact',
                'recommended_actions': [
                    'Optimize calling times',
                    'Improve DID reputation',
                    'Review area code strategy'
                ]
            })
            
        # Cost per minute optimization
        if efficiency['cost_per_minute'] > settings.max_cost_per_minute:
            opportunities.append({
                'type': 'cost_per_minute',
                'priority': 'medium',
                'title': 'Optimize Call Duration',
                'description': f'Cost per minute ${efficiency["cost_per_minute"]:.6f} exceeds target',
                'potential_savings': 'Reduce per-minute costs',
                'recommended_actions': [
                    'Optimize conversation flow',
                    'Improve AI response times',
                    'Reduce unnecessary call duration'
                ]
            })
            
        return opportunities
        
    async def _get_cost_predictions(self, campaign_id: uuid.UUID) -> Dict[str, Any]:
        """Get cost predictions based on current trends."""
        # Get recent performance data
        recent_data = await self._get_cost_trends(campaign_id, datetime.utcnow() - timedelta(days=3))
        
        if not recent_data['daily_trends']:
            return {
                'daily_cost_prediction': 0,
                'weekly_cost_prediction': 0,
                'monthly_cost_prediction': 0,
                'confidence': 0
            }
            
        # Calculate average daily cost from recent data
        recent_costs = [day['total_cost'] for day in recent_data['daily_trends'] if day['total_cost'] > 0]
        if recent_costs:
            avg_daily_cost = np.mean(recent_costs)
            
            return {
                'daily_cost_prediction': round(avg_daily_cost, 4),
                'weekly_cost_prediction': round(avg_daily_cost * 7, 2),
                'monthly_cost_prediction': round(avg_daily_cost * 30, 2),
                'confidence': min(len(recent_costs) * 25, 100)  # Confidence based on data points
            }
        else:
            return {
                'daily_cost_prediction': 0,
                'weekly_cost_prediction': 0,
                'monthly_cost_prediction': 0,
                'confidence': 0
            }

# Async context manager for cost optimization
async def get_cost_optimization_engine():
    """Get cost optimization engine with proper session management."""
    async with CostOptimizationEngine() as engine:
        yield engine 