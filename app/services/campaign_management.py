"""
Campaign Management Service
Handles campaign creation, management, A/B testing, and optimization.
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
    Campaign, Lead, CampaignStatus, LeadStatus, ABTestVariant,
    CampaignAnalytics, CallLog, CallStatus, CallDisposition
)
from app.config import settings
import json
import random
import numpy as np
from scipy import stats
import pandas as pd

logger = logging.getLogger(__name__)

class CampaignManagementService:
    """
    Comprehensive campaign management with A/B testing and optimization.
    """
    
    def __init__(self):
        self.session = AsyncSessionLocal()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        
    async def create_campaign(self, campaign_data: Dict[str, Any]) -> Campaign:
        """
        Create a new campaign with optimization features.
        """
        try:
            # Create campaign
            campaign = Campaign(
                id=uuid.uuid4(),
                name=campaign_data['name'],
                description=campaign_data.get('description', ''),
                script_template=campaign_data['script_template'],
                max_concurrent_calls=campaign_data.get('max_concurrent_calls', 100),
                max_daily_budget=campaign_data.get('max_daily_budget', 1000.0),
                cost_per_minute_limit=campaign_data.get('cost_per_minute_limit', 0.025),
                start_time=campaign_data.get('start_time'),
                end_time=campaign_data.get('end_time'),
                daily_start_hour=campaign_data.get('daily_start_hour', 8),
                daily_end_hour=campaign_data.get('daily_end_hour', 21),
                timezone=campaign_data.get('timezone', 'America/New_York'),
                ab_test_enabled=campaign_data.get('ab_test_enabled', False),
                ab_test_variants=campaign_data.get('ab_test_variants', {}),
                status=CampaignStatus.DRAFT
            )
            
            self.session.add(campaign)
            await self.session.commit()
            
            # Create A/B test variants if enabled
            if campaign.ab_test_enabled and campaign.ab_test_variants:
                await self._create_ab_test_variants(campaign.id, campaign.ab_test_variants)
            
            logger.info(f"Created campaign: {campaign.name} (ID: {campaign.id})")
            return campaign
            
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            await self.session.rollback()
            raise
            
    async def _create_ab_test_variants(self, campaign_id: uuid.UUID, variants_config: Dict[str, Any]):
        """
        Create A/B test variants for a campaign.
        """
        try:
            for variant_name, config in variants_config.items():
                variant = ABTestVariant(
                    id=uuid.uuid4(),
                    campaign_id=campaign_id,
                    variant_name=variant_name,
                    variant_type=config.get('type', 'script'),
                    config_json=config,
                    traffic_percentage=config.get('traffic_percentage', 50.0),
                    is_active=True
                )
                self.session.add(variant)
                
            await self.session.commit()
            logger.info(f"Created A/B test variants for campaign {campaign_id}")
            
        except Exception as e:
            logger.error(f"Error creating A/B test variants: {e}")
            await self.session.rollback()
            raise
            
    async def upload_leads(self, campaign_id: uuid.UUID, leads_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Upload leads to a campaign with optimization and validation.
        """
        results = {
            'total_leads': len(leads_data),
            'valid_leads': 0,
            'invalid_leads': 0,
            'duplicate_leads': 0,
            'dnc_leads': 0
        }
        
        try:
            # Get campaign
            campaign = await self._get_campaign_by_id(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
                
            # Process leads
            for lead_data in leads_data:
                try:
                    # Validate lead data
                    if not self._validate_lead_data(lead_data):
                        results['invalid_leads'] += 1
                        continue
                        
                    # Check for duplicates
                    if await self._is_duplicate_lead(campaign_id, lead_data['phone']):
                        results['duplicate_leads'] += 1
                        continue
                        
                    # Check DNC status (if service is available)
                    # is_dnc = await self._check_dnc_status(lead_data['phone'])
                    is_dnc = False  # Placeholder
                    
                    if is_dnc:
                        results['dnc_leads'] += 1
                        continue
                        
                    # Create lead
                    lead = Lead(
                        id=uuid.uuid4(),
                        campaign_id=campaign_id,
                        first_name=lead_data.get('first_name', ''),
                        last_name=lead_data.get('last_name', ''),
                        email=lead_data.get('email', ''),
                        phone=lead_data['phone'],
                        company=lead_data.get('company', ''),
                        title=lead_data.get('title', ''),
                        area_code=lead_data['phone'][2:5] if len(lead_data['phone']) >= 5 else None,
                        state=lead_data.get('state', ''),
                        city=lead_data.get('city', ''),
                        timezone=lead_data.get('timezone', 'America/New_York'),
                        status=LeadStatus.NEW,
                        score=await self._calculate_lead_score(lead_data),
                        priority=lead_data.get('priority', 5),
                        dnc_status=is_dnc,
                        consent_status=lead_data.get('consent_status', False),
                        custom_fields=lead_data.get('custom_fields', {})
                    )
                    
                    self.session.add(lead)
                    results['valid_leads'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing lead {lead_data.get('phone', 'unknown')}: {e}")
                    results['invalid_leads'] += 1
                    
            # Update campaign lead count
            campaign.total_leads = results['valid_leads']
            await self.session.commit()
            
            logger.info(f"Uploaded {results['valid_leads']} leads to campaign {campaign_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error uploading leads: {e}")
            await self.session.rollback()
            raise
            
    def _validate_lead_data(self, lead_data: Dict[str, Any]) -> bool:
        """
        Validate lead data structure and required fields.
        """
        required_fields = ['phone']
        
        for field in required_fields:
            if field not in lead_data or not lead_data[field]:
                return False
                
        # Validate phone number format
        phone = lead_data['phone']
        if not phone.startswith('+1') or len(phone) != 12:
            return False
            
        return True
        
    async def _is_duplicate_lead(self, campaign_id: uuid.UUID, phone: str) -> bool:
        """
        Check if lead already exists in campaign.
        """
        stmt = select(Lead).where(
            Lead.campaign_id == campaign_id,
            Lead.phone == phone
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
        
    async def _calculate_lead_score(self, lead_data: Dict[str, Any]) -> float:
        """
        Calculate predictive lead score based on available data.
        """
        score = 0.0
        
        # Base score
        score += 50.0
        
        # Company information bonus
        if lead_data.get('company'):
            score += 10.0
            
        # Title/role bonus
        if lead_data.get('title'):
            title_lower = lead_data['title'].lower()
            if any(keyword in title_lower for keyword in ['ceo', 'president', 'owner', 'founder']):
                score += 20.0
            elif any(keyword in title_lower for keyword in ['vp', 'vice president', 'director']):
                score += 15.0
            elif any(keyword in title_lower for keyword in ['manager', 'head']):
                score += 10.0
                
        # Email bonus
        if lead_data.get('email'):
            score += 5.0
            
        # Geographic bonus (high-value area codes)
        area_code = lead_data.get('phone', '')[2:5] if len(lead_data.get('phone', '')) >= 5 else None
        if area_code in ['212', '415', '310', '617', '202']:  # High-value area codes
            score += 15.0
            
        # Custom fields bonus
        custom_fields = lead_data.get('custom_fields', {})
        if custom_fields.get('revenue'):
            try:
                revenue = float(custom_fields['revenue'])
                if revenue > 10000000:  # $10M+
                    score += 25.0
                elif revenue > 1000000:  # $1M+
                    score += 15.0
                elif revenue > 100000:  # $100K+
                    score += 10.0
            except (ValueError, TypeError):
                pass
                
        return min(score, 100.0)  # Cap at 100
        
    async def start_campaign(self, campaign_id: uuid.UUID) -> bool:
        """
        Start a campaign with pre-flight checks.
        """
        try:
            campaign = await self._get_campaign_by_id(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
                
            # Pre-flight checks
            if not await self._pre_flight_checks(campaign):
                return False
                
            # Update campaign status
            campaign.status = CampaignStatus.ACTIVE
            await self.session.commit()
            
            logger.info(f"Started campaign: {campaign.name} (ID: {campaign_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error starting campaign {campaign_id}: {e}")
            await self.session.rollback()
            return False
            
    async def _pre_flight_checks(self, campaign: Campaign) -> bool:
        """
        Perform pre-flight checks before starting campaign.
        """
        checks = []
        
        # Check if campaign has leads
        stmt = select(func.count(Lead.id)).where(
            Lead.campaign_id == campaign.id,
            Lead.status == LeadStatus.NEW
        )
        result = await self.session.execute(stmt)
        lead_count = result.scalar()
        
        if lead_count == 0:
            logger.error(f"Campaign {campaign.id} has no leads")
            return False
            
        # Check if script template exists
        if not campaign.script_template:
            logger.error(f"Campaign {campaign.id} has no script template")
            return False
            
        # Check budget
        if campaign.max_daily_budget <= 0:
            logger.error(f"Campaign {campaign.id} has invalid budget")
            return False
            
        # Check DID availability
        # This would check if there are enough DIDs available
        # For now, we'll skip this check
        
        logger.info(f"Pre-flight checks passed for campaign {campaign.id}")
        return True
        
    async def pause_campaign(self, campaign_id: uuid.UUID, reason: str = None) -> bool:
        """
        Pause a campaign and stop all active calls.
        """
        try:
            campaign = await self._get_campaign_by_id(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
                
            campaign.status = CampaignStatus.PAUSED
            await self.session.commit()
            
            logger.info(f"Paused campaign: {campaign.name} (ID: {campaign_id}), Reason: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error pausing campaign {campaign_id}: {e}")
            await self.session.rollback()
            return False
            
    async def get_campaign_performance(self, campaign_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get comprehensive campaign performance metrics.
        """
        try:
            campaign = await self._get_campaign_by_id(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
                
            # Get call metrics
            call_metrics = await self._get_call_metrics(campaign_id)
            
            # Get conversion metrics
            conversion_metrics = await self._get_conversion_metrics(campaign_id)
            
            # Get cost metrics
            cost_metrics = await self._get_cost_metrics(campaign_id)
            
            # Get quality metrics
            quality_metrics = await self._get_quality_metrics(campaign_id)
            
            # Get A/B test results if enabled
            ab_test_results = {}
            if campaign.ab_test_enabled:
                ab_test_results = await self._get_ab_test_results(campaign_id)
                
            # Get optimization recommendations
            recommendations = await self._get_optimization_recommendations(campaign_id)
            
            return {
                'campaign_id': str(campaign_id),
                'campaign_name': campaign.name,
                'status': campaign.status.value,
                'call_metrics': call_metrics,
                'conversion_metrics': conversion_metrics,
                'cost_metrics': cost_metrics,
                'quality_metrics': quality_metrics,
                'ab_test_results': ab_test_results,
                'recommendations': recommendations,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign performance: {e}")
            raise
            
    async def _get_call_metrics(self, campaign_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get call-related metrics for a campaign.
        """
        # Total calls
        total_calls_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id
        )
        total_calls = await self.session.execute(total_calls_stmt)
        total_calls = total_calls.scalar()
        
        # Answered calls
        answered_calls_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.status == CallStatus.ANSWERED
        )
        answered_calls = await self.session.execute(answered_calls_stmt)
        answered_calls = answered_calls.scalar()
        
        # Completed calls
        completed_calls_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.status == CallStatus.COMPLETED
        )
        completed_calls = await self.session.execute(completed_calls_stmt)
        completed_calls = completed_calls.scalar()
        
        # Average call duration
        avg_duration_stmt = select(func.avg(CallLog.duration_seconds)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.status == CallStatus.COMPLETED
        )
        avg_duration = await self.session.execute(avg_duration_stmt)
        avg_duration = avg_duration.scalar() or 0
        
        # Answer rate
        answer_rate = (answered_calls / total_calls * 100) if total_calls > 0 else 0
        
        return {
            'total_calls': total_calls,
            'answered_calls': answered_calls,
            'completed_calls': completed_calls,
            'answer_rate': round(answer_rate, 2),
            'avg_duration_seconds': round(avg_duration, 2)
        }
        
    async def _get_conversion_metrics(self, campaign_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get conversion-related metrics for a campaign.
        """
        # Transfers
        transfers_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.disposition == CallDisposition.TRANSFER
        )
        transfers = await self.session.execute(transfers_stmt)
        transfers = transfers.scalar()
        
        # Qualified leads
        qualified_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.disposition == CallDisposition.QUALIFIED
        )
        qualified = await self.session.execute(qualified_stmt)
        qualified = qualified.scalar()
        
        # Total answered calls for conversion rate calculation
        answered_calls_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.status == CallStatus.ANSWERED
        )
        answered_calls = await self.session.execute(answered_calls_stmt)
        answered_calls = answered_calls.scalar()
        
        # Conversion rates
        transfer_rate = (transfers / answered_calls * 100) if answered_calls > 0 else 0
        qualification_rate = (qualified / answered_calls * 100) if answered_calls > 0 else 0
        
        return {
            'transfers': transfers,
            'qualified_leads': qualified,
            'transfer_rate': round(transfer_rate, 2),
            'qualification_rate': round(qualification_rate, 2)
        }
        
    async def _get_cost_metrics(self, campaign_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get cost-related metrics for a campaign.
        """
        # Total cost
        total_cost_stmt = select(func.sum(CallLog.total_cost)).where(
            CallLog.campaign_id == campaign_id
        )
        total_cost = await self.session.execute(total_cost_stmt)
        total_cost = total_cost.scalar() or 0
        
        # Total calls for cost per call calculation
        total_calls_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id
        )
        total_calls = await self.session.execute(total_calls_stmt)
        total_calls = total_calls.scalar()
        
        # Transfers for cost per transfer calculation
        transfers_stmt = select(func.count(CallLog.id)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.disposition == CallDisposition.TRANSFER
        )
        transfers = await self.session.execute(transfers_stmt)
        transfers = transfers.scalar()
        
        # Cost calculations
        cost_per_call = total_cost / total_calls if total_calls > 0 else 0
        cost_per_transfer = total_cost / transfers if transfers > 0 else 0
        
        return {
            'total_cost': round(total_cost, 4),
            'cost_per_call': round(cost_per_call, 4),
            'cost_per_transfer': round(cost_per_transfer, 4)
        }
        
    async def _get_quality_metrics(self, campaign_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get quality-related metrics for a campaign.
        """
        # Average AI response time
        ai_response_stmt = select(func.avg(CallLog.ai_response_time_ms)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.ai_response_time_ms.isnot(None)
        )
        ai_response = await self.session.execute(ai_response_stmt)
        ai_response = ai_response.scalar() or 0
        
        # Average audio quality
        audio_quality_stmt = select(func.avg(CallLog.audio_quality_score)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.audio_quality_score.isnot(None)
        )
        audio_quality = await self.session.execute(audio_quality_stmt)
        audio_quality = audio_quality.scalar() or 0
        
        # Average AI confidence
        ai_confidence_stmt = select(func.avg(CallLog.ai_confidence_score)).where(
            CallLog.campaign_id == campaign_id,
            CallLog.ai_confidence_score.isnot(None)
        )
        ai_confidence = await self.session.execute(ai_confidence_stmt)
        ai_confidence = ai_confidence.scalar() or 0
        
        return {
            'avg_ai_response_time_ms': round(ai_response, 2),
            'avg_audio_quality_score': round(audio_quality, 2),
            'avg_ai_confidence_score': round(ai_confidence, 2)
        }
        
    async def _get_ab_test_results(self, campaign_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get A/B test results for a campaign.
        """
        # Get all active variants
        variants_stmt = select(ABTestVariant).where(
            ABTestVariant.campaign_id == campaign_id,
            ABTestVariant.is_active == True
        )
        variants_result = await self.session.execute(variants_stmt)
        variants = variants_result.scalars().all()
        
        results = {}
        
        for variant in variants:
            # Calculate statistical significance
            statistical_data = await self._calculate_ab_test_significance(variant)
            
            results[variant.variant_name] = {
                'total_calls': variant.total_calls,
                'conversion_rate': variant.conversion_rate,
                'cost_per_conversion': variant.cost_per_conversion,
                'traffic_percentage': variant.traffic_percentage,
                'confidence_level': variant.confidence_level,
                'p_value': variant.p_value,
                'is_winner': variant.is_winner,
                'statistical_significance': statistical_data
            }
            
        return results
        
    async def _calculate_ab_test_significance(self, variant: ABTestVariant) -> Dict[str, Any]:
        """
        Calculate statistical significance for A/B test variant.
        """
        # This is a simplified implementation
        # In production, you'd use proper statistical testing
        
        if variant.total_calls < 100:
            return {
                'significance': 'insufficient_data',
                'message': 'Need more data for statistical significance'
            }
            
        # Mock statistical calculation
        # In production, use proper A/B testing statistics
        if variant.p_value < 0.05:
            return {
                'significance': 'significant',
                'confidence': variant.confidence_level,
                'message': f'Statistically significant with {variant.confidence_level}% confidence'
            }
        else:
            return {
                'significance': 'not_significant',
                'confidence': variant.confidence_level,
                'message': 'Not statistically significant'
            }
            
    async def _get_optimization_recommendations(self, campaign_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Generate optimization recommendations for a campaign.
        """
        recommendations = []
        
        # Get campaign metrics
        call_metrics = await self._get_call_metrics(campaign_id)
        conversion_metrics = await self._get_conversion_metrics(campaign_id)
        cost_metrics = await self._get_cost_metrics(campaign_id)
        
        # Low answer rate recommendation
        if call_metrics['answer_rate'] < 15:
            recommendations.append({
                'type': 'answer_rate',
                'priority': 'high',
                'title': 'Low Answer Rate Detected',
                'description': f"Answer rate is {call_metrics['answer_rate']}%, consider adjusting call times or DID strategy",
                'suggested_action': 'Review optimal calling hours and DID reputation'
            })
            
        # Low conversion rate recommendation
        if conversion_metrics['transfer_rate'] < 5:
            recommendations.append({
                'type': 'conversion_rate',
                'priority': 'high',
                'title': 'Low Transfer Rate',
                'description': f"Transfer rate is {conversion_metrics['transfer_rate']}%, script optimization needed",
                'suggested_action': 'Review and optimize AI script for better qualification'
            })
            
        # High cost per transfer recommendation
        if cost_metrics['cost_per_transfer'] > 0.14:
            recommendations.append({
                'type': 'cost_optimization',
                'priority': 'medium',
                'title': 'High Cost Per Transfer',
                'description': f"Cost per transfer is ${cost_metrics['cost_per_transfer']:.4f}, above target of $0.14",
                'suggested_action': 'Review call duration and qualification criteria'
            })
            
        # Add time-based recommendations
        time_recommendations = await self._get_time_based_recommendations(campaign_id)
        recommendations.extend(time_recommendations)
        
        return recommendations
        
    async def _get_time_based_recommendations(self, campaign_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Get time-based optimization recommendations.
        """
        recommendations = []
        
        # Analyze call performance by hour
        # This would require more complex analytics
        # For now, return placeholder recommendations
        
        recommendations.append({
            'type': 'timing_optimization',
            'priority': 'medium',
            'title': 'Optimal Call Times',
            'description': 'Consider adjusting call times based on performance data',
            'suggested_action': 'Review hourly performance metrics and adjust scheduling'
        })
        
        return recommendations
        
    async def _get_campaign_by_id(self, campaign_id: uuid.UUID) -> Optional[Campaign]:
        """
        Get campaign by ID.
        """
        stmt = select(Campaign).where(Campaign.id == campaign_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def list_campaigns(self, status: Optional[CampaignStatus] = None) -> List[Campaign]:
        """
        List campaigns with optional status filter.
        """
        stmt = select(Campaign)
        
        if status:
            stmt = stmt.where(Campaign.status == status)
            
        stmt = stmt.order_by(Campaign.created_at.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
        
    async def get_campaign_leads(self, campaign_id: uuid.UUID, status: Optional[LeadStatus] = None) -> List[Lead]:
        """
        Get leads for a campaign with optional status filter.
        """
        stmt = select(Lead).where(Lead.campaign_id == campaign_id)
        
        if status:
            stmt = stmt.where(Lead.status == status)
            
        stmt = stmt.order_by(Lead.score.desc(), Lead.created_at.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

# Async context manager for campaign management
async def get_campaign_management_service():
    """Get campaign management service with proper session management."""
    async with CampaignManagementService() as service:
        yield service 