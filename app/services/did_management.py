import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.config import settings
from app.database import get_db
from app.models import DIDPool, CallLog, CampaignAnalytics, Campaign

logger = logging.getLogger(__name__)

class DIDStatus(Enum):
    ACTIVE = "active"
    WARMING = "warming"
    COOLING = "cooling"
    QUARANTINE = "quarantine"
    RETIRED = "retired"

@dataclass
class DIDHealthScore:
    did_id: int
    phone_number: str
    health_score: float
    answer_rate: float
    spam_complaints: int
    carrier_filtering: bool
    reputation_score: float
    recommendation: str

class DIDManagementService:
    def __init__(self):
        self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.spam_check_apis = [
            'https://api.truecaller.com/v1/spam-check',
            'https://api.hiya.com/v1/reputation'
        ]
        
    async def initialize_did_pool(self, campaign_id: int, area_codes: List[str], 
                                 count_per_area: int = 5) -> Dict[str, Any]:
        """Initialize DID pool for a campaign"""
        try:
            results = {
                'purchased': [],
                'failed': [],
                'total_cost': 0.0
            }
            
            async with get_db() as db:
                for area_code in area_codes:
                    try:
                        # Purchase DIDs from Twilio
                        dids = await self._purchase_dids(area_code, count_per_area)
                        
                        for did_info in dids:
                            # Create DID record
                            did_record = DIDPool(
                                campaign_id=campaign_id,
                                phone_number=did_info['phone_number'],
                                area_code=area_code,
                                status='warming',
                                health_score=100.0,
                                purchase_cost=did_info['cost'],
                                monthly_cost=did_info['monthly_cost'],
                                twilio_sid=did_info['sid'],
                                purchased_at=datetime.utcnow()
                            )
                            
                            db.add(did_record)
                            results['purchased'].append(did_info)
                            results['total_cost'] += did_info['cost']
                        
                    except Exception as e:
                        logger.error(f"Error purchasing DIDs for area code {area_code}: {e}")
                        results['failed'].append({'area_code': area_code, 'error': str(e)})
                
                await db.commit()
                
            # Start warming process
            await self._start_warming_process(campaign_id)
            
            logger.info(f"Initialized DID pool for campaign {campaign_id}: {len(results['purchased'])} DIDs purchased")
            return results
            
        except Exception as e:
            logger.error(f"Error initializing DID pool: {e}")
            raise
    
    async def _purchase_dids(self, area_code: str, count: int) -> List[Dict[str, Any]]:
        """Purchase DIDs from Twilio"""
        try:
            dids = []
            
            # Search for available numbers
            available_numbers = self.twilio_client.available_phone_numbers('US').local.list(
                area_code=area_code,
                limit=count
            )
            
            for number in available_numbers:
                try:
                    # Purchase the number
                    incoming_phone_number = self.twilio_client.incoming_phone_numbers.create(
                        phone_number=number.phone_number,
                        voice_url=f"{settings.BASE_URL}/webhooks/twilio/voice",
                        voice_method='POST',
                        status_callback=f"{settings.BASE_URL}/webhooks/twilio/number-status",
                        status_callback_method='POST'
                    )
                    
                    dids.append({
                        'phone_number': number.phone_number,
                        'sid': incoming_phone_number.sid,
                        'cost': 1.00,  # Standard Twilio cost
                        'monthly_cost': 1.00,
                        'capabilities': {
                            'voice': True,
                            'sms': number.capabilities.get('sms', False),
                            'mms': number.capabilities.get('mms', False)
                        }
                    })
                    
                except TwilioRestException as e:
                    logger.error(f"Error purchasing number {number.phone_number}: {e}")
                    continue
            
            return dids
            
        except Exception as e:
            logger.error(f"Error purchasing DIDs: {e}")
            return []
    
    async def get_available_did(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        """Get an available DID for making calls"""
        try:
            async with get_db() as db:
                # Get healthy DIDs for the campaign
                available_query = select(DIDPool).where(
                    and_(
                        DIDPool.campaign_id == campaign_id,
                        DIDPool.status.in_(['active', 'warming']),
                        DIDPool.health_score > 70,
                        DIDPool.in_use == False,
                        DIDPool.daily_call_count < DIDPool.daily_limit
                    )
                ).order_by(DIDPool.health_score.desc(), DIDPool.last_used.asc())
                
                available_dids = await db.execute(available_query)
                available_did = available_dids.scalar_one_or_none()
                
                if not available_did:
                    # Try to get a warming DID if no active ones
                    warming_query = select(DIDPool).where(
                        and_(
                            DIDPool.campaign_id == campaign_id,
                            DIDPool.status == 'warming',
                            DIDPool.health_score > 60,
                            DIDPool.in_use == False
                        )
                    ).order_by(DIDPool.health_score.desc())
                    
                    warming_dids = await db.execute(warming_query)
                    available_did = warming_dids.scalar_one_or_none()
                
                if available_did:
                    return {
                        'id': available_did.id,
                        'phone_number': available_did.phone_number,
                        'area_code': available_did.area_code,
                        'health_score': available_did.health_score,
                        'status': available_did.status
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting available DID: {e}")
            return None
    
    async def mark_did_in_use(self, did_id: int) -> bool:
        """Mark DID as in use"""
        try:
            async with get_db() as db:
                # Update DID status
                update_query = update(DIDPool).where(DIDPool.id == did_id).values(
                    in_use=True,
                    last_used=datetime.utcnow(),
                    daily_call_count=DIDPool.daily_call_count + 1,
                    total_calls=DIDPool.total_calls + 1
                )
                await db.execute(update_query)
                await db.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Error marking DID in use: {e}")
            return False
    
    async def release_did(self, campaign_id: int, did_id: Optional[int] = None) -> bool:
        """Release DID after call completion"""
        try:
            async with get_db() as db:
                if did_id:
                    # Release specific DID
                    update_query = update(DIDPool).where(DIDPool.id == did_id).values(
                        in_use=False
                    )
                    await db.execute(update_query)
                else:
                    # Release all DIDs for campaign
                    update_query = update(DIDPool).where(
                        DIDPool.campaign_id == campaign_id
                    ).values(in_use=False)
                    await db.execute(update_query)
                
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error releasing DID: {e}")
            return False
    
    async def analyze_did_health(self, did_id: int) -> DIDHealthScore:
        """Analyze DID health and reputation"""
        try:
            async with get_db() as db:
                # Get DID record
                did_query = select(DIDPool).where(DIDPool.id == did_id)
                did_record = await db.execute(did_query)
                did_record = did_record.scalar_one_or_none()
                
                if not did_record:
                    raise ValueError(f"DID {did_id} not found")
                
                # Calculate metrics
                health_metrics = await self._calculate_health_metrics(did_record)
                
                # Check spam reputation
                spam_score = await self._check_spam_reputation(did_record.phone_number)
                
                # Generate health score
                health_score = await self._generate_health_score(health_metrics, spam_score)
                
                return DIDHealthScore(
                    did_id=did_id,
                    phone_number=did_record.phone_number,
                    health_score=health_score['overall_score'],
                    answer_rate=health_metrics['answer_rate'],
                    spam_complaints=spam_score['complaints'],
                    carrier_filtering=spam_score['filtered'],
                    reputation_score=spam_score['reputation'],
                    recommendation=health_score['recommendation']
                )
                
        except Exception as e:
            logger.error(f"Error analyzing DID health: {e}")
            raise
    
    async def _calculate_health_metrics(self, did_record: Any) -> Dict[str, Any]:
        """Calculate health metrics for a DID"""
        try:
            async with get_db() as db:
                # Get call statistics
                stats_query = select(
                    func.count(CallLog.id).label('total_calls'),
                    func.sum(func.case([(CallLog.call_status == 'answered', 1)], else_=0)).label('answered_calls'),
                    func.sum(func.case([(CallLog.call_status == 'busy', 1)], else_=0)).label('busy_calls'),
                    func.sum(func.case([(CallLog.call_status == 'failed', 1)], else_=0)).label('failed_calls'),
                    func.avg(CallLog.call_duration).label('avg_duration')
                ).where(
                    and_(
                        CallLog.did_id == did_record.id,
                        CallLog.call_start >= datetime.utcnow() - timedelta(days=30)
                    )
                )
                
                stats = await db.execute(stats_query)
                stats = stats.first()
                
                # Calculate rates
                total_calls = stats.total_calls or 0
                answered_calls = stats.answered_calls or 0
                busy_calls = stats.busy_calls or 0
                failed_calls = stats.failed_calls or 0
                
                answer_rate = (answered_calls / total_calls * 100) if total_calls > 0 else 0
                busy_rate = (busy_calls / total_calls * 100) if total_calls > 0 else 0
                failure_rate = (failed_calls / total_calls * 100) if total_calls > 0 else 0
                
                return {
                    'total_calls': total_calls,
                    'answer_rate': answer_rate,
                    'busy_rate': busy_rate,
                    'failure_rate': failure_rate,
                    'avg_duration': stats.avg_duration or 0
                }
                
        except Exception as e:
            logger.error(f"Error calculating health metrics: {e}")
            return {}
    
    async def _check_spam_reputation(self, phone_number: str) -> Dict[str, Any]:
        """Check spam reputation for a phone number"""
        try:
            reputation_data = {
                'complaints': 0,
                'filtered': False,
                'reputation': 100.0,
                'sources': []
            }
            
            # Check multiple spam databases
            for api_url in self.spam_check_apis:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            api_url,
                            params={'phone_number': phone_number},
                            headers={'Authorization': f'Bearer {settings.SPAM_CHECK_API_KEY}'}
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                # Parse response based on API
                                if 'truecaller' in api_url:
                                    reputation_data['complaints'] += data.get('spam_score', 0)
                                    reputation_data['filtered'] = data.get('is_spam', False)
                                elif 'hiya' in api_url:
                                    reputation_data['reputation'] = min(
                                        reputation_data['reputation'],
                                        data.get('reputation_score', 100)
                                    )
                                
                                reputation_data['sources'].append({
                                    'source': api_url,
                                    'data': data
                                })
                                
                except Exception as e:
                    logger.warning(f"Error checking spam reputation with {api_url}: {e}")
                    continue
            
            return reputation_data
            
        except Exception as e:
            logger.error(f"Error checking spam reputation: {e}")
            return {
                'complaints': 0,
                'filtered': False,
                'reputation': 100.0,
                'sources': []
            }
    
    async def _generate_health_score(self, health_metrics: Dict[str, Any], 
                                   spam_score: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall health score and recommendation"""
        try:
            # Base score from call metrics
            base_score = 100.0
            
            # Answer rate impact (0-40 points)
            answer_rate = health_metrics.get('answer_rate', 0)
            if answer_rate >= 20:
                answer_score = 40
            elif answer_rate >= 15:
                answer_score = 30
            elif answer_rate >= 10:
                answer_score = 20
            else:
                answer_score = 10
            
            # Failure rate impact (0-30 points)
            failure_rate = health_metrics.get('failure_rate', 0)
            if failure_rate <= 5:
                failure_score = 30
            elif failure_rate <= 10:
                failure_score = 20
            elif failure_rate <= 20:
                failure_score = 10
            else:
                failure_score = 0
            
            # Spam reputation impact (0-30 points)
            spam_reputation = spam_score.get('reputation', 100)
            if spam_reputation >= 90:
                spam_score_points = 30
            elif spam_reputation >= 70:
                spam_score_points = 20
            elif spam_reputation >= 50:
                spam_score_points = 10
            else:
                spam_score_points = 0
            
            # Calculate overall score
            overall_score = answer_score + failure_score + spam_score_points
            
            # Generate recommendation
            if overall_score >= 80:
                recommendation = "Excellent - Continue using"
            elif overall_score >= 60:
                recommendation = "Good - Monitor closely"
            elif overall_score >= 40:
                recommendation = "Warning - Reduce usage"
            else:
                recommendation = "Poor - Consider retirement"
            
            return {
                'overall_score': overall_score,
                'answer_score': answer_score,
                'failure_score': failure_score,
                'spam_score': spam_score_points,
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f"Error generating health score: {e}")
            return {
                'overall_score': 50.0,
                'recommendation': "Error - Manual review needed"
            }
    
    async def rotate_dids(self, campaign_id: int) -> Dict[str, Any]:
        """Rotate DIDs for a campaign"""
        try:
            async with get_db() as db:
                # Get all DIDs for campaign
                dids_query = select(DIDPool).where(DIDPool.campaign_id == campaign_id)
                dids = await db.execute(dids_query)
                dids = dids.scalars().all()
                
                rotation_results = {
                    'analyzed': 0,
                    'retired': 0,
                    'quarantined': 0,
                    'activated': 0,
                    'purchased': 0
                }
                
                for did in dids:
                    # Analyze health
                    health_score = await self.analyze_did_health(did.id)
                    
                    # Update health score
                    update_query = update(DIDPool).where(DIDPool.id == did.id).values(
                        health_score=health_score.health_score,
                        last_health_check=datetime.utcnow()
                    )
                    await db.execute(update_query)
                    
                    # Take action based on health
                    if health_score.health_score < 30:
                        # Retire poor performing DIDs
                        await self._retire_did(did.id)
                        rotation_results['retired'] += 1
                    elif health_score.health_score < 50:
                        # Quarantine marginal DIDs
                        await self._quarantine_did(did.id)
                        rotation_results['quarantined'] += 1
                    elif health_score.health_score > 70 and did.status == 'warming':
                        # Activate warmed DIDs
                        await self._activate_did(did.id)
                        rotation_results['activated'] += 1
                    
                    rotation_results['analyzed'] += 1
                
                # Purchase new DIDs if needed
                active_count = len([d for d in dids if d.status == 'active'])
                if active_count < 5:  # Maintain minimum of 5 active DIDs
                    # Get campaign area codes
                    campaign_query = select(Campaign).where(Campaign.id == campaign_id)
                    campaign = await db.execute(campaign_query)
                    campaign = campaign.scalar_one_or_none()
                    
                    if campaign and campaign.area_codes:
                        needed_dids = 5 - active_count
                        area_codes = campaign.area_codes.split(',')
                        
                        purchase_result = await self.initialize_did_pool(
                            campaign_id, area_codes[:1], needed_dids
                        )
                        rotation_results['purchased'] = len(purchase_result['purchased'])
                
                await db.commit()
                
                logger.info(f"Rotated DIDs for campaign {campaign_id}: {rotation_results}")
                return rotation_results
                
        except Exception as e:
            logger.error(f"Error rotating DIDs: {e}")
            raise
    
    async def _retire_did(self, did_id: int):
        """Retire a DID"""
        try:
            async with get_db() as db:
                # Update status
                update_query = update(DIDPool).where(DIDPool.id == did_id).values(
                    status='retired',
                    retired_at=datetime.utcnow()
                )
                await db.execute(update_query)
                
                # Release from Twilio (optional - may want to keep for analytics)
                # await self._release_twilio_number(did_id)
                
        except Exception as e:
            logger.error(f"Error retiring DID: {e}")
    
    async def _quarantine_did(self, did_id: int):
        """Quarantine a DID"""
        try:
            async with get_db() as db:
                update_query = update(DIDPool).where(DIDPool.id == did_id).values(
                    status='quarantine',
                    quarantine_until=datetime.utcnow() + timedelta(days=7)
                )
                await db.execute(update_query)
                
        except Exception as e:
            logger.error(f"Error quarantining DID: {e}")
    
    async def _activate_did(self, did_id: int):
        """Activate a DID"""
        try:
            async with get_db() as db:
                update_query = update(DIDPool).where(DIDPool.id == did_id).values(
                    status='active',
                    activated_at=datetime.utcnow()
                )
                await db.execute(update_query)
                
        except Exception as e:
            logger.error(f"Error activating DID: {e}")
    
    async def _start_warming_process(self, campaign_id: int):
        """Start warming process for new DIDs"""
        try:
            # Warming process would involve:
            # 1. Gradually increasing call volume
            # 2. Making calls to known good numbers
            # 3. Monitoring for any reputation issues
            
            logger.info(f"Started warming process for campaign {campaign_id}")
            
        except Exception as e:
            logger.error(f"Error starting warming process: {e}")
    
    async def get_did_pool_status(self, campaign_id: int) -> Dict[str, Any]:
        """Get status of DID pool for a campaign"""
        try:
            async with get_db() as db:
                # Get DID statistics
                stats_query = select(
                    DIDPool.status,
                    func.count(DIDPool.id).label('count'),
                    func.avg(DIDPool.health_score).label('avg_health_score')
                ).where(
                    DIDPool.campaign_id == campaign_id
                ).group_by(DIDPool.status)
                
                stats = await db.execute(stats_query)
                stats = stats.all()
                
                status_summary = {}
                for stat in stats:
                    status_summary[stat.status] = {
                        'count': stat.count,
                        'avg_health_score': stat.avg_health_score
                    }
                
                return {
                    'campaign_id': campaign_id,
                    'status_summary': status_summary,
                    'last_updated': datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Error getting DID pool status: {e}")
            return {}

# Global instance
did_management_service = DIDManagementService() 