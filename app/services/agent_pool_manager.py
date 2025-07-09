"""
Agent Pool Management Service

This service manages virtual AI agents that simulate human-like dialing patterns
to avoid carrier detection and improve contact rates.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID
import json
import logging

from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models import AgentPool, AgentNumber, CallLog, DIDPool, NumberReputation
from app.config import settings

logger = logging.getLogger(__name__)


class AgentPoolManager:
    """Manages virtual AI agents with human-like characteristics"""
    
    def __init__(self):
        self.active_agents: Dict[UUID, Dict] = {}
        self.agent_schedules: Dict[UUID, Dict] = {}
        self.performance_cache: Dict[UUID, Dict] = {}
        
    async def create_agent_pool(
        self,
        name: str,
        region: str,
        personality_config: Dict[str, Any],
        active_hours: Dict[str, str],
        dialing_pattern: Dict[str, Any]
    ) -> AgentPool:
        """Create a new agent pool with specified characteristics"""
        
        async with AsyncSessionLocal() as session:
            try:
                # Validate personality configuration
                self._validate_personality_config(personality_config)
                
                # Create agent pool
                agent_pool = AgentPool(
                    name=name,
                    region=region,
                    personality_config=personality_config,
                    active_hours=active_hours,
                    dialing_pattern=dialing_pattern
                )
                
                session.add(agent_pool)
                await session.commit()
                await session.refresh(agent_pool)
                
                # Initialize agent in memory
                await self._initialize_agent_in_memory(agent_pool)
                
                logger.info(f"Created agent pool: {name} in region: {region}")
                return agent_pool
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create agent pool: {e}")
                raise
    
    def _validate_personality_config(self, config: Dict[str, Any]) -> None:
        """Validate agent personality configuration"""
        required_fields = ['voice_type', 'conversation_style', 'response_timing']
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required personality field: {field}")
        
        # Validate voice type
        valid_voices = ['professional_male', 'professional_female', 'casual_male', 'casual_female']
        if config['voice_type'] not in valid_voices:
            raise ValueError(f"Invalid voice type: {config['voice_type']}")
        
        # Validate conversation style
        valid_styles = ['formal', 'casual', 'friendly', 'professional']
        if config['conversation_style'] not in valid_styles:
            raise ValueError(f"Invalid conversation style: {config['conversation_style']}")
    
    async def _initialize_agent_in_memory(self, agent_pool: AgentPool) -> None:
        """Initialize agent state in memory for fast access"""
        agent_id = agent_pool.id
        
        # Cache agent configuration
        self.active_agents[agent_id] = {
            'name': agent_pool.name,
            'region': agent_pool.region,
            'personality': agent_pool.personality_config,
            'active_hours': agent_pool.active_hours,
            'dialing_pattern': agent_pool.dialing_pattern,
            'is_active': agent_pool.is_active,
            'last_call_time': None,
            'current_calls': 0,
            'daily_call_count': 0,
            'rest_until': None
        }
        
        # Initialize performance cache
        self.performance_cache[agent_id] = {
            'success_rate': agent_pool.success_rate,
            'answer_rate': agent_pool.answer_rate,
            'reputation_score': agent_pool.reputation_score,
            'last_updated': datetime.utcnow()
        }
    
    async def get_optimal_agent_for_call(
        self,
        target_phone: str,
        campaign_id: UUID,
        area_code: str = None,
        preferred_agents: List[UUID] = None
    ) -> Optional[AgentPool]:
        """Select the best agent for a specific call using intelligent routing"""
        
        async with AsyncSessionLocal() as session:
            try:
                # Get all available agents
                available_agents = await self._get_available_agents(session, area_code)
                
                if not available_agents:
                    logger.warning("No available agents found for call")
                    return None
                
                # Apply preference filtering
                if preferred_agents:
                    available_agents = [
                        agent for agent in available_agents 
                        if agent.id in preferred_agents
                    ]
                
                # Score agents based on multiple factors
                scored_agents = await self._score_agents_for_call(
                    session, available_agents, target_phone, area_code
                )
                
                if not scored_agents:
                    return None
                
                # Select agent using weighted random selection
                selected_agent = self._weighted_agent_selection(scored_agents)
                
                # Update agent state
                await self._update_agent_state_for_call(selected_agent.id)
                
                logger.info(f"Selected agent {selected_agent.name} for call to {target_phone}")
                return selected_agent
                
            except Exception as e:
                logger.error(f"Failed to select optimal agent: {e}")
                return None
    
    async def _get_available_agents(
        self,
        session: AsyncSession,
        area_code: str = None
    ) -> List[AgentPool]:
        """Get all agents that are currently available for calls"""
        
        current_time = datetime.utcnow()
        
        # Build query for available agents
        query = select(AgentPool).where(
            and_(
                AgentPool.is_active == True,
                AgentPool.is_blocked == False
            )
        ).options(selectinload(AgentPool.agent_numbers))
        
        result = await session.execute(query)
        all_agents = result.scalars().all()
        
        available_agents = []
        for agent in all_agents:
            # Check if agent is in active hours
            if not self._is_agent_in_active_hours(agent, current_time):
                continue
            
            # Check if agent is resting
            if await self._is_agent_resting(agent.id):
                continue
            
            # Check if agent has numbers assigned
            if not agent.agent_numbers:
                continue
            
            # Check if agent has healthy numbers
            if not await self._has_healthy_numbers(session, agent.id):
                continue
            
            available_agents.append(agent)
        
        return available_agents
    
    def _is_agent_in_active_hours(self, agent: AgentPool, current_time: datetime) -> bool:
        """Check if agent is currently in active hours"""
        active_hours = agent.active_hours
        timezone = active_hours.get('timezone', 'UTC')
        
        # For now, simplified check - in production, handle timezones properly
        start_hour = int(active_hours.get('start', '09:00').split(':')[0])
        end_hour = int(active_hours.get('end', '17:00').split(':')[0])
        
        current_hour = current_time.hour
        
        return start_hour <= current_hour <= end_hour
    
    async def _is_agent_resting(self, agent_id: UUID) -> bool:
        """Check if agent is in rest period"""
        if agent_id not in self.active_agents:
            return False
        
        agent_state = self.active_agents[agent_id]
        rest_until = agent_state.get('rest_until')
        
        if rest_until and datetime.utcnow() < rest_until:
            return True
        
        return False
    
    async def _has_healthy_numbers(self, session: AsyncSession, agent_id: UUID) -> bool:
        """Check if agent has healthy numbers available"""
        query = select(AgentNumber).where(
            and_(
                AgentNumber.agent_id == agent_id,
                AgentNumber.is_blocked == False,
                AgentNumber.health_score > 5.0  # Minimum health threshold
            )
        )
        
        result = await session.execute(query)
        healthy_numbers = result.scalars().all()
        
        return len(healthy_numbers) > 0
    
    async def _score_agents_for_call(
        self,
        session: AsyncSession,
        agents: List[AgentPool],
        target_phone: str,
        area_code: str = None
    ) -> List[tuple]:
        """Score agents based on performance, geographic match, and availability"""
        
        scored_agents = []
        
        for agent in agents:
            score = 0.0
            
            # Performance score (40% weight)
            performance_score = self._calculate_performance_score(agent)
            score += performance_score * 0.4
            
            # Geographic match (30% weight)
            geographic_score = await self._calculate_geographic_score(
                session, agent, area_code
            )
            score += geographic_score * 0.3
            
            # Availability/freshness score (20% weight)
            availability_score = self._calculate_availability_score(agent)
            score += availability_score * 0.2
            
            # Number health score (10% weight)
            number_health_score = await self._calculate_number_health_score(
                session, agent.id
            )
            score += number_health_score * 0.1
            
            scored_agents.append((agent, score))
        
        # Sort by score (highest first)
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        
        return scored_agents
    
    def _calculate_performance_score(self, agent: AgentPool) -> float:
        """Calculate agent performance score based on success/answer rates"""
        success_rate = agent.success_rate or 0.0
        answer_rate = agent.answer_rate or 0.0
        reputation_score = agent.reputation_score or 5.0
        
        # Normalize reputation score to 0-1 scale
        normalized_reputation = reputation_score / 10.0
        
        # Weighted performance score
        performance_score = (
            success_rate * 0.4 +
            answer_rate * 0.4 +
            normalized_reputation * 0.2
        )
        
        return min(performance_score, 1.0)
    
    async def _calculate_geographic_score(
        self,
        session: AsyncSession,
        agent: AgentPool,
        area_code: str = None
    ) -> float:
        """Calculate geographic matching score"""
        if not area_code:
            return 0.5  # Neutral score if no area code provided
        
        # Get agent's numbers and their area codes
        query = select(AgentNumber, DIDPool.phone_number).join(
            DIDPool, AgentNumber.did_id == DIDPool.id
        ).where(AgentNumber.agent_id == agent.id)
        
        result = await session.execute(query)
        agent_numbers = result.all()
        
        if not agent_numbers:
            return 0.0
        
        # Check for exact area code match
        exact_matches = 0
        for agent_number, phone_number in agent_numbers:
            if phone_number and phone_number.startswith(f"+1{area_code}"):
                exact_matches += 1
        
        if exact_matches > 0:
            return 1.0  # Perfect match
        
        # Check for regional proximity (simplified)
        regional_score = self._calculate_regional_proximity(agent.region, area_code)
        return regional_score
    
    def _calculate_regional_proximity(self, agent_region: str, area_code: str) -> float:
        """Calculate regional proximity score"""
        # Simplified regional mapping
        regional_codes = {
            'east_coast': ['212', '646', '718', '917', '347', '929'],
            'west_coast': ['310', '323', '424', '213', '818', '747'],
            'central': ['312', '773', '872', '469', '214', '972'],
            'south': ['404', '678', '470', '305', '786', '954']
        }
        
        if agent_region in regional_codes:
            if area_code in regional_codes[agent_region]:
                return 0.8  # Good regional match
        
        return 0.3  # Poor regional match
    
    def _calculate_availability_score(self, agent: AgentPool) -> float:
        """Calculate agent availability/freshness score"""
        if agent.id not in self.active_agents:
            return 0.5
        
        agent_state = self.active_agents[agent.id]
        
        # Factor in current call load
        current_calls = agent_state.get('current_calls', 0)
        if current_calls >= 3:  # Maximum concurrent calls
            return 0.0
        
        # Factor in recent usage
        last_call_time = agent_state.get('last_call_time')
        if last_call_time:
            time_since_last = (datetime.utcnow() - last_call_time).total_seconds()
            if time_since_last < 300:  # Less than 5 minutes
                return 0.3
            elif time_since_last < 900:  # Less than 15 minutes
                return 0.7
        
        return 1.0  # Fresh agent
    
    async def _calculate_number_health_score(
        self,
        session: AsyncSession,
        agent_id: UUID
    ) -> float:
        """Calculate average health score of agent's numbers"""
        query = select(func.avg(AgentNumber.health_score)).where(
            and_(
                AgentNumber.agent_id == agent_id,
                AgentNumber.is_blocked == False
            )
        )
        
        result = await session.execute(query)
        avg_health = result.scalar()
        
        if avg_health is None:
            return 0.0
        
        return avg_health / 10.0  # Normalize to 0-1 scale
    
    def _weighted_agent_selection(self, scored_agents: List[tuple]) -> AgentPool:
        """Select agent using weighted random selection"""
        if not scored_agents:
            return None
        
        # Create weights based on scores
        agents = [agent for agent, score in scored_agents]
        weights = [score for agent, score in scored_agents]
        
        # Add minimum weight to prevent zero weights
        weights = [max(w, 0.1) for w in weights]
        
        # Weighted random selection
        total_weight = sum(weights)
        if total_weight == 0:
            return agents[0]  # Fallback to first agent
        
        random_value = random.uniform(0, total_weight)
        current_weight = 0
        
        for agent, weight in zip(agents, weights):
            current_weight += weight
            if random_value <= current_weight:
                return agent
        
        return agents[0]  # Fallback
    
    async def _update_agent_state_for_call(self, agent_id: UUID) -> None:
        """Update agent state when a call is initiated"""
        if agent_id not in self.active_agents:
            return
        
        agent_state = self.active_agents[agent_id]
        
        # Update state
        agent_state['last_call_time'] = datetime.utcnow()
        agent_state['current_calls'] += 1
        agent_state['daily_call_count'] += 1
        
        # Check if agent needs rest
        dialing_pattern = agent_state.get('dialing_pattern', {})
        max_calls_per_hour = dialing_pattern.get('max_calls_per_hour', 20)
        
        if agent_state['daily_call_count'] >= max_calls_per_hour:
            rest_hours = dialing_pattern.get('rest_hours', 4)
            agent_state['rest_until'] = datetime.utcnow() + timedelta(hours=rest_hours)
    
    async def complete_call(
        self,
        agent_id: UUID,
        call_successful: bool,
        call_answered: bool,
        call_duration: int = 0
    ) -> None:
        """Update agent state when a call is completed"""
        
        # Update in-memory state
        if agent_id in self.active_agents:
            self.active_agents[agent_id]['current_calls'] -= 1
            self.active_agents[agent_id]['current_calls'] = max(0, self.active_agents[agent_id]['current_calls'])
        
        # Update database performance metrics
        await self._update_agent_performance(agent_id, call_successful, call_answered, call_duration)
    
    async def _update_agent_performance(
        self,
        agent_id: UUID,
        call_successful: bool,
        call_answered: bool,
        call_duration: int
    ) -> None:
        """Update agent performance metrics in database"""
        
        async with AsyncSessionLocal() as session:
            try:
                # Get current stats
                query = select(AgentPool).where(AgentPool.id == agent_id)
                result = await session.execute(query)
                agent = result.scalar_one_or_none()
                
                if not agent:
                    return
                
                # Get call count for this agent
                call_count_query = select(func.count(CallLog.id)).where(
                    CallLog.agent_pool_id == agent_id
                )
                call_count_result = await session.execute(call_count_query)
                total_calls = call_count_result.scalar() or 0
                
                # Calculate new success rate
                if call_successful:
                    success_count = int(agent.success_rate * total_calls) + 1
                else:
                    success_count = int(agent.success_rate * total_calls)
                
                new_success_rate = success_count / max(total_calls, 1)
                
                # Calculate new answer rate
                if call_answered:
                    answer_count = int(agent.answer_rate * total_calls) + 1
                else:
                    answer_count = int(agent.answer_rate * total_calls)
                
                new_answer_rate = answer_count / max(total_calls, 1)
                
                # Update agent
                update_query = update(AgentPool).where(
                    AgentPool.id == agent_id
                ).values(
                    success_rate=new_success_rate,
                    answer_rate=new_answer_rate,
                    last_used_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                await session.execute(update_query)
                await session.commit()
                
                # Update performance cache
                if agent_id in self.performance_cache:
                    self.performance_cache[agent_id].update({
                        'success_rate': new_success_rate,
                        'answer_rate': new_answer_rate,
                        'last_updated': datetime.utcnow()
                    })
                
                logger.info(f"Updated performance for agent {agent_id}: success={new_success_rate:.2f}, answer={new_answer_rate:.2f}")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update agent performance: {e}")
    
    async def get_agent_performance_summary(self, agent_id: UUID) -> Dict[str, Any]:
        """Get comprehensive performance summary for an agent"""
        
        async with AsyncSessionLocal() as session:
            try:
                # Get agent details
                query = select(AgentPool).where(AgentPool.id == agent_id)
                result = await session.execute(query)
                agent = result.scalar_one_or_none()
                
                if not agent:
                    return {}
                
                # Get call statistics
                call_stats_query = select(
                    func.count(CallLog.id).label('total_calls'),
                    func.sum(func.case((CallLog.call_status == 'completed', 1), else_=0)).label('successful_calls'),
                    func.sum(func.case((CallLog.call_answered.is_(True), 1), else_=0)).label('answered_calls'),
                    func.avg(CallLog.call_duration).label('avg_duration')
                ).where(CallLog.agent_pool_id == agent_id)
                
                stats_result = await session.execute(call_stats_query)
                stats = stats_result.first()
                
                # Get number assignment count
                number_count_query = select(func.count(AgentNumber.id)).where(
                    AgentNumber.agent_id == agent_id
                )
                number_count_result = await session.execute(number_count_query)
                number_count = number_count_result.scalar() or 0
                
                return {
                    'agent_id': str(agent_id),
                    'name': agent.name,
                    'region': agent.region,
                    'is_active': agent.is_active,
                    'success_rate': agent.success_rate,
                    'answer_rate': agent.answer_rate,
                    'reputation_score': agent.reputation_score,
                    'total_calls': stats.total_calls or 0,
                    'successful_calls': stats.successful_calls or 0,
                    'answered_calls': stats.answered_calls or 0,
                    'avg_call_duration': float(stats.avg_duration) if stats.avg_duration else 0.0,
                    'assigned_numbers': number_count,
                    'last_used': agent.last_used_at.isoformat() if agent.last_used_at else None,
                    'created_at': agent.created_at.isoformat(),
                    'current_state': self.active_agents.get(agent_id, {})
                }
                
            except Exception as e:
                logger.error(f"Failed to get agent performance summary: {e}")
                return {}
    
    async def reset_daily_counters(self) -> None:
        """Reset daily counters for all agents (call this daily)"""
        for agent_id in self.active_agents:
            self.active_agents[agent_id]['daily_call_count'] = 0
            self.active_agents[agent_id]['rest_until'] = None
        
        logger.info("Reset daily counters for all agents")


# Global instance
agent_pool_manager = AgentPoolManager() 