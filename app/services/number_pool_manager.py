"""
Number Pool Management Service

This service manages dynamic distribution of phone numbers across agents,
monitors number health, and optimizes routing to maximize contact rates
while avoiding carrier spam detection.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
import logging

from sqlalchemy import select, update, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models import (
    AgentPool, AgentNumber, DIDPool, NumberReputation, 
    CallLog, Campaign, CNAMRegistration
)
from app.config import settings
from app.services.agent_pool_manager import agent_pool_manager

logger = logging.getLogger(__name__)


class NumberPoolManager:
    """Manages dynamic number pools for optimized call routing"""
    
    def __init__(self):
        self.number_assignments: Dict[UUID, List[UUID]] = {}  # agent_id -> [number_ids]
        self.number_health_cache: Dict[UUID, Dict] = {}
        self.area_code_mappings: Dict[str, List[UUID]] = {}
        self.rotation_schedules: Dict[UUID, Dict] = {}
        
    async def initialize_number_pools(self) -> None:
        """Initialize number pools and assignments"""
        async with AsyncSessionLocal() as session:
            try:
                # Load existing assignments
                query = select(AgentNumber).options(
                    selectinload(AgentNumber.agent_pool),
                    selectinload(AgentNumber.did)
                )
                result = await session.execute(query)
                assignments = result.scalars().all()
                
                # Build assignment cache
                for assignment in assignments:
                    agent_id = assignment.agent_id
                    if agent_id not in self.number_assignments:
                        self.number_assignments[agent_id] = []
                    self.number_assignments[agent_id].append(assignment.did_id)
                
                # Build area code mappings
                await self._build_area_code_mappings(session)
                
                # Cache number health
                await self._cache_number_health(session)
                
                logger.info("Number pools initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize number pools: {e}")
                raise
    
    async def _build_area_code_mappings(self, session: AsyncSession) -> None:
        """Build area code to number mappings for geographic matching"""
        query = select(DIDPool.id, DIDPool.phone_number).where(
            DIDPool.is_active == True
        )
        result = await session.execute(query)
        numbers = result.all()
        
        self.area_code_mappings.clear()
        
        for did_id, phone_number in numbers:
            if phone_number and len(phone_number) >= 5:
                # Extract area code from +1XXXXXXXXXX format
                area_code = phone_number[2:5] if phone_number.startswith('+1') else phone_number[:3]
                
                if area_code not in self.area_code_mappings:
                    self.area_code_mappings[area_code] = []
                
                self.area_code_mappings[area_code].append(did_id)
    
    async def _cache_number_health(self, session: AsyncSession) -> None:
        """Cache number health scores for fast access"""
        query = select(
            AgentNumber.did_id,
            AgentNumber.health_score,
            AgentNumber.spam_score,
            AgentNumber.is_blocked,
            AgentNumber.calls_today,
            AgentNumber.calls_this_week,
            AgentNumber.last_used_at
        ).where(AgentNumber.is_blocked == False)
        
        result = await session.execute(query)
        health_data = result.all()
        
        self.number_health_cache.clear()
        
        for did_id, health_score, spam_score, is_blocked, calls_today, calls_this_week, last_used_at in health_data:
            self.number_health_cache[did_id] = {
                'health_score': health_score,
                'spam_score': spam_score,
                'is_blocked': is_blocked,
                'calls_today': calls_today,
                'calls_this_week': calls_this_week,
                'last_used_at': last_used_at
            }
    
    async def assign_numbers_to_agent(
        self,
        agent_id: UUID,
        number_count: int = 20,
        preferred_area_codes: List[str] = None,
        campaign_id: UUID = None
    ) -> List[UUID]:
        """Assign optimal numbers to an agent based on criteria"""
        
        async with AsyncSessionLocal() as session:
            try:
                # Get available numbers
                available_numbers = await self._get_available_numbers(
                    session, preferred_area_codes, campaign_id
                )
                
                if len(available_numbers) < number_count:
                    logger.warning(f"Only {len(available_numbers)} numbers available, requested {number_count}")
                
                # Score and select best numbers
                scored_numbers = await self._score_numbers_for_agent(
                    session, agent_id, available_numbers, preferred_area_codes
                )
                
                # Select top numbers
                selected_numbers = [
                    number for number, score in scored_numbers[:number_count]
                ]
                
                # Create assignments
                assignments = []
                for i, did_id in enumerate(selected_numbers):
                    assignment = AgentNumber(
                        agent_id=agent_id,
                        did_id=did_id,
                        is_primary=(i == 0),  # First number is primary
                        assigned_at=datetime.utcnow()
                    )
                    assignments.append(assignment)
                    session.add(assignment)
                
                await session.commit()
                
                # Update cache
                if agent_id not in self.number_assignments:
                    self.number_assignments[agent_id] = []
                self.number_assignments[agent_id].extend(selected_numbers)
                
                logger.info(f"Assigned {len(selected_numbers)} numbers to agent {agent_id}")
                return selected_numbers
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to assign numbers to agent: {e}")
                raise
    
    async def _get_available_numbers(
        self,
        session: AsyncSession,
        preferred_area_codes: List[str] = None,
        campaign_id: UUID = None
    ) -> List[UUID]:
        """Get available numbers for assignment"""
        
        # Base query for available numbers
        query = select(DIDPool.id).where(
            and_(
                DIDPool.is_active == True,
                DIDPool.is_available == True
            )
        )
        
        # Exclude numbers already assigned
        assigned_numbers_query = select(AgentNumber.did_id).where(
            AgentNumber.is_blocked == False
        )
        assigned_result = await session.execute(assigned_numbers_query)
        assigned_numbers = [row[0] for row in assigned_result.all()]
        
        if assigned_numbers:
            query = query.where(~DIDPool.id.in_(assigned_numbers))
        
        # Filter by area codes if specified
        if preferred_area_codes:
            area_code_filters = []
            for area_code in preferred_area_codes:
                area_code_filters.append(
                    DIDPool.phone_number.like(f'+1{area_code}%')
                )
            query = query.where(or_(*area_code_filters))
        
        result = await session.execute(query)
        return [row[0] for row in result.all()]
    
    async def _score_numbers_for_agent(
        self,
        session: AsyncSession,
        agent_id: UUID,
        available_numbers: List[UUID],
        preferred_area_codes: List[str] = None
    ) -> List[Tuple[UUID, float]]:
        """Score numbers based on health, reputation, and geographic match"""
        
        scored_numbers = []
        
        for did_id in available_numbers:
            score = 0.0
            
            # Health score (40% weight)
            health_score = await self._calculate_number_health_score(session, did_id)
            score += health_score * 0.4
            
            # Reputation score (30% weight)
            reputation_score = await self._calculate_number_reputation_score(session, did_id)
            score += reputation_score * 0.3
            
            # Geographic match (20% weight)
            geographic_score = await self._calculate_geographic_match_score(
                session, did_id, preferred_area_codes
            )
            score += geographic_score * 0.2
            
            # Usage freshness (10% weight)
            freshness_score = await self._calculate_number_freshness_score(session, did_id)
            score += freshness_score * 0.1
            
            scored_numbers.append((did_id, score))
        
        # Sort by score (highest first)
        scored_numbers.sort(key=lambda x: x[1], reverse=True)
        
        return scored_numbers
    
    async def _calculate_number_health_score(self, session: AsyncSession, did_id: UUID) -> float:
        """Calculate number health score"""
        if did_id in self.number_health_cache:
            health_data = self.number_health_cache[did_id]
            return health_data['health_score'] / 10.0
        
        # Fallback to database
        query = select(AgentNumber.health_score).where(
            AgentNumber.did_id == did_id
        )
        result = await session.execute(query)
        health_score = result.scalar()
        
        return (health_score or 10.0) / 10.0
    
    async def _calculate_number_reputation_score(self, session: AsyncSession, did_id: UUID) -> float:
        """Calculate number reputation score"""
        query = select(NumberReputation.reputation_score).where(
            NumberReputation.did_id == did_id
        ).order_by(desc(NumberReputation.last_checked_at)).limit(1)
        
        result = await session.execute(query)
        reputation_score = result.scalar()
        
        if reputation_score is None:
            return 0.5  # Neutral score for unknown reputation
        
        return reputation_score / 10.0
    
    async def _calculate_geographic_match_score(
        self,
        session: AsyncSession,
        did_id: UUID,
        preferred_area_codes: List[str] = None
    ) -> float:
        """Calculate geographic matching score"""
        if not preferred_area_codes:
            return 0.5  # Neutral score if no preference
        
        # Get phone number
        query = select(DIDPool.phone_number).where(DIDPool.id == did_id)
        result = await session.execute(query)
        phone_number = result.scalar()
        
        if not phone_number:
            return 0.0
        
        # Extract area code
        area_code = phone_number[2:5] if phone_number.startswith('+1') else phone_number[:3]
        
        # Check for exact match
        if area_code in preferred_area_codes:
            return 1.0
        
        # Check for regional proximity
        return self._calculate_regional_proximity_score(area_code, preferred_area_codes)
    
    def _calculate_regional_proximity_score(self, area_code: str, preferred_area_codes: List[str]) -> float:
        """Calculate regional proximity score"""
        # Simplified regional groupings
        regional_groups = {
            'northeast': ['212', '646', '718', '917', '347', '929', '201', '973', '732'],
            'southeast': ['404', '678', '470', '305', '786', '954', '561', '321', '407'],
            'midwest': ['312', '773', '872', '469', '214', '972', '713', '281', '832'],
            'west': ['310', '323', '424', '213', '818', '747', '415', '650', '925'],
            'southwest': ['602', '623', '480', '520', '702', '775', '505', '575'],
            'northwest': ['206', '253', '425', '360', '509', '503', '541', '971']
        }
        
        # Find region for target area code
        target_region = None
        for region, codes in regional_groups.items():
            if area_code in codes:
                target_region = region
                break
        
        if not target_region:
            return 0.2  # Unknown region
        
        # Check if any preferred area codes are in the same region
        for preferred_code in preferred_area_codes:
            if preferred_code in regional_groups[target_region]:
                return 0.7  # Good regional match
        
        return 0.3  # Different region
    
    async def _calculate_number_freshness_score(self, session: AsyncSession, did_id: UUID) -> float:
        """Calculate number freshness score based on recent usage"""
        if did_id in self.number_health_cache:
            health_data = self.number_health_cache[did_id]
            last_used_at = health_data['last_used_at']
            
            if last_used_at is None:
                return 1.0  # Never used = fresh
            
            time_since_used = (datetime.utcnow() - last_used_at).total_seconds()
            
            # Freshness scoring
            if time_since_used > 86400:  # > 24 hours
                return 1.0
            elif time_since_used > 3600:  # > 1 hour
                return 0.8
            elif time_since_used > 300:  # > 5 minutes
                return 0.6
            else:
                return 0.3
        
        return 0.5  # Unknown
    
    async def get_optimal_number_for_call(
        self,
        agent_id: UUID,
        target_phone: str,
        area_code: str = None
    ) -> Optional[UUID]:
        """Get the optimal number for a specific call"""
        
        async with AsyncSessionLocal() as session:
            try:
                # Get agent's assigned numbers
                agent_numbers = self.number_assignments.get(agent_id, [])
                
                if not agent_numbers:
                    logger.warning(f"No numbers assigned to agent {agent_id}")
                    return None
                
                # Filter healthy numbers
                healthy_numbers = []
                for did_id in agent_numbers:
                    if await self._is_number_healthy_for_call(session, did_id):
                        healthy_numbers.append(did_id)
                
                if not healthy_numbers:
                    logger.warning(f"No healthy numbers available for agent {agent_id}")
                    return None
                
                # Score numbers for this specific call
                scored_numbers = []
                for did_id in healthy_numbers:
                    score = await self._score_number_for_call(
                        session, did_id, target_phone, area_code
                    )
                    scored_numbers.append((did_id, score))
                
                # Sort by score
                scored_numbers.sort(key=lambda x: x[1], reverse=True)
                
                # Select best number
                selected_number = scored_numbers[0][0]
                
                # Update number usage
                await self._update_number_usage(session, selected_number)
                
                logger.info(f"Selected number {selected_number} for call to {target_phone}")
                return selected_number
                
            except Exception as e:
                logger.error(f"Failed to get optimal number for call: {e}")
                return None
    
    async def _is_number_healthy_for_call(self, session: AsyncSession, did_id: UUID) -> bool:
        """Check if number is healthy enough for a call"""
        if did_id in self.number_health_cache:
            health_data = self.number_health_cache[did_id]
            
            # Check basic health
            if health_data['health_score'] < 5.0:
                return False
            
            # Check spam score
            if health_data['spam_score'] > 7.0:
                return False
            
            # Check daily limits
            if health_data['calls_today'] >= 100:  # Daily limit
                return False
            
            # Check weekly limits
            if health_data['calls_this_week'] >= 500:  # Weekly limit
                return False
            
            return True
        
        # Fallback to database check
        query = select(AgentNumber).where(
            and_(
                AgentNumber.did_id == did_id,
                AgentNumber.is_blocked == False,
                AgentNumber.health_score >= 5.0,
                AgentNumber.calls_today < 100
            )
        )
        
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def _score_number_for_call(
        self,
        session: AsyncSession,
        did_id: UUID,
        target_phone: str,
        area_code: str = None
    ) -> float:
        """Score a number for a specific call"""
        score = 0.0
        
        # Geographic match (50% weight)
        if area_code:
            geographic_score = await self._calculate_geographic_match_score(
                session, did_id, [area_code]
            )
            score += geographic_score * 0.5
        
        # Health score (30% weight)
        health_score = await self._calculate_number_health_score(session, did_id)
        score += health_score * 0.3
        
        # Freshness score (20% weight)
        freshness_score = await self._calculate_number_freshness_score(session, did_id)
        score += freshness_score * 0.2
        
        return score
    
    async def _update_number_usage(self, session: AsyncSession, did_id: UUID) -> None:
        """Update number usage statistics"""
        try:
            # Update database
            update_query = update(AgentNumber).where(
                AgentNumber.did_id == did_id
            ).values(
                calls_today=AgentNumber.calls_today + 1,
                calls_this_week=AgentNumber.calls_this_week + 1,
                last_used_at=datetime.utcnow()
            )
            
            await session.execute(update_query)
            await session.commit()
            
            # Update cache
            if did_id in self.number_health_cache:
                self.number_health_cache[did_id]['calls_today'] += 1
                self.number_health_cache[did_id]['calls_this_week'] += 1
                self.number_health_cache[did_id]['last_used_at'] = datetime.utcnow()
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update number usage: {e}")
    
    async def monitor_number_health(self, did_id: UUID) -> Dict[str, Any]:
        """Monitor and return number health metrics"""
        
        async with AsyncSessionLocal() as session:
            try:
                # Get number details
                query = select(AgentNumber, DIDPool.phone_number).join(
                    DIDPool, AgentNumber.did_id == DIDPool.id
                ).where(AgentNumber.did_id == did_id)
                
                result = await session.execute(query)
                number_data = result.first()
                
                if not number_data:
                    return {}
                
                agent_number, phone_number = number_data
                
                # Get recent call performance
                recent_calls_query = select(
                    func.count(CallLog.id).label('total_calls'),
                    func.sum(func.case((CallLog.call_answered.is_(True), 1), else_=0)).label('answered_calls'),
                    func.avg(CallLog.call_duration).label('avg_duration')
                ).where(
                    and_(
                        CallLog.phone_number == phone_number,
                        CallLog.created_at >= datetime.utcnow() - timedelta(days=7)
                    )
                )
                
                stats_result = await session.execute(recent_calls_query)
                stats = stats_result.first()
                
                # Get reputation data
                reputation_query = select(NumberReputation).where(
                    NumberReputation.did_id == did_id
                ).order_by(desc(NumberReputation.last_checked_at)).limit(1)
                
                reputation_result = await session.execute(reputation_query)
                reputation = reputation_result.scalar_one_or_none()
                
                return {
                    'did_id': str(did_id),
                    'phone_number': phone_number,
                    'health_score': agent_number.health_score,
                    'spam_score': agent_number.spam_score,
                    'is_blocked': agent_number.is_blocked,
                    'calls_today': agent_number.calls_today,
                    'calls_this_week': agent_number.calls_this_week,
                    'last_used_at': agent_number.last_used_at.isoformat() if agent_number.last_used_at else None,
                    'recent_performance': {
                        'total_calls': stats.total_calls or 0,
                        'answered_calls': stats.answered_calls or 0,
                        'answer_rate': (stats.answered_calls / stats.total_calls) if stats.total_calls > 0 else 0,
                        'avg_duration': float(stats.avg_duration) if stats.avg_duration else 0.0
                    },
                    'reputation': {
                        'score': reputation.reputation_score if reputation else 5.0,
                        'spam_flagged': reputation.is_spam_flagged if reputation else False,
                        'current_label': reputation.current_label if reputation else None,
                        'last_checked': reputation.last_checked_at.isoformat() if reputation else None
                    }
                }
                
            except Exception as e:
                logger.error(f"Failed to monitor number health: {e}")
                return {}
    
    async def rotate_numbers_for_agent(self, agent_id: UUID) -> None:
        """Rotate numbers for an agent to maintain freshness"""
        
        async with AsyncSessionLocal() as session:
            try:
                # Get current assignments
                current_assignments = self.number_assignments.get(agent_id, [])
                
                # Identify numbers that need rotation
                numbers_to_rotate = []
                for did_id in current_assignments:
                    if did_id in self.number_health_cache:
                        health_data = self.number_health_cache[did_id]
                        
                        # Rotate if health is low or usage is high
                        if (health_data['health_score'] < 6.0 or 
                            health_data['calls_this_week'] > 300):
                            numbers_to_rotate.append(did_id)
                
                if not numbers_to_rotate:
                    return
                
                # Get replacement numbers
                replacement_count = len(numbers_to_rotate)
                available_numbers = await self._get_available_numbers(session)
                
                if len(available_numbers) < replacement_count:
                    logger.warning(f"Not enough replacement numbers available for agent {agent_id}")
                    return
                
                # Score and select replacements
                scored_numbers = await self._score_numbers_for_agent(
                    session, agent_id, available_numbers
                )
                
                replacement_numbers = [
                    number for number, score in scored_numbers[:replacement_count]
                ]
                
                # Remove old assignments
                delete_query = select(AgentNumber).where(
                    and_(
                        AgentNumber.agent_id == agent_id,
                        AgentNumber.did_id.in_(numbers_to_rotate)
                    )
                )
                
                result = await session.execute(delete_query)
                old_assignments = result.scalars().all()
                
                for assignment in old_assignments:
                    await session.delete(assignment)
                
                # Create new assignments
                for did_id in replacement_numbers:
                    new_assignment = AgentNumber(
                        agent_id=agent_id,
                        did_id=did_id,
                        assigned_at=datetime.utcnow()
                    )
                    session.add(new_assignment)
                
                await session.commit()
                
                # Update cache
                if agent_id in self.number_assignments:
                    for old_did in numbers_to_rotate:
                        self.number_assignments[agent_id].remove(old_did)
                    self.number_assignments[agent_id].extend(replacement_numbers)
                
                logger.info(f"Rotated {len(numbers_to_rotate)} numbers for agent {agent_id}")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to rotate numbers for agent: {e}")
    
    async def get_pool_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pool statistics"""
        
        async with AsyncSessionLocal() as session:
            try:
                # Total numbers
                total_numbers_query = select(func.count(DIDPool.id)).where(
                    DIDPool.is_active == True
                )
                total_numbers = await session.execute(total_numbers_query)
                
                # Assigned numbers
                assigned_numbers_query = select(func.count(AgentNumber.id)).where(
                    AgentNumber.is_blocked == False
                )
                assigned_numbers = await session.execute(assigned_numbers_query)
                
                # Available numbers
                available_numbers_query = select(func.count(DIDPool.id)).where(
                    and_(
                        DIDPool.is_active == True,
                        DIDPool.is_available == True
                    )
                )
                available_numbers = await session.execute(available_numbers_query)
                
                # Health distribution
                health_distribution_query = select(
                    func.count(AgentNumber.id).label('count'),
                    func.case(
                        (AgentNumber.health_score >= 8.0, 'excellent'),
                        (AgentNumber.health_score >= 6.0, 'good'),
                        (AgentNumber.health_score >= 4.0, 'fair'),
                        else_='poor'
                    ).label('health_category')
                ).group_by('health_category')
                
                health_result = await session.execute(health_distribution_query)
                health_distribution = {row.health_category: row.count for row in health_result}
                
                # Agent assignments
                agent_assignments_query = select(
                    AgentNumber.agent_id,
                    func.count(AgentNumber.id).label('number_count')
                ).group_by(AgentNumber.agent_id)
                
                agent_result = await session.execute(agent_assignments_query)
                agent_assignments = {str(row.agent_id): row.number_count for row in agent_result}
                
                return {
                    'total_numbers': total_numbers.scalar() or 0,
                    'assigned_numbers': assigned_numbers.scalar() or 0,
                    'available_numbers': available_numbers.scalar() or 0,
                    'health_distribution': health_distribution,
                    'agent_assignments': agent_assignments,
                    'area_code_distribution': {
                        code: len(numbers) for code, numbers in self.area_code_mappings.items()
                    }
                }
                
            except Exception as e:
                logger.error(f"Failed to get pool statistics: {e}")
                return {}


# Global instance
number_pool_manager = NumberPoolManager() 