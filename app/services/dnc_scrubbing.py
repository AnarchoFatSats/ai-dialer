"""
DNC Scrubbing Service
Handles National DNC Registry, state-specific registries, and company suppression lists.
"""

import asyncio
import ftplib
import io
import csv
import zipfile
import logging
import httpx
from typing import List, Set, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models import DNCRegistry, Lead, LeadStatus
from app.config import settings, DNC_REGISTRY_CONFIG
import pandas as pd
from bs4 import BeautifulSoup
import re
from pathlib import Path
import tempfile
import os

logger = logging.getLogger(__name__)

class DNCScrubbingService:
    """
    Comprehensive DNC scrubbing service that handles multiple DNC sources.
    """
    
    def __init__(self):
        self.session = AsyncSessionLocal()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.dnc_sources = {
            'national': self._process_national_dnc,
            'state_tx': self._process_state_dnc,
            'state_fl': self._process_state_dnc,
            'state_ny': self._process_state_dnc,
            'state_ca': self._process_state_dnc,
            'company': self._process_company_dnc
        }
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        
    async def full_dnc_scrub(self) -> Dict[str, int]:
        """
        Perform a complete DNC scrub from all sources.
        Returns counts of numbers processed by source.
        """
        logger.info("Starting full DNC scrub")
        results = {}
        
        try:
            # Download and process each DNC source
            for source_name, processor in self.dnc_sources.items():
                try:
                    count = await processor(source_name)
                    results[source_name] = count
                    logger.info(f"Processed {count} numbers from {source_name}")
                except Exception as e:
                    logger.error(f"Error processing {source_name}: {e}")
                    results[source_name] = 0
                    
            # Update lead statuses based on DNC registry
            scrubbed_leads = await self._update_lead_dnc_status()
            results['leads_scrubbed'] = scrubbed_leads
            
            # Clean up old DNC entries
            cleaned_entries = await self._cleanup_old_dnc_entries()
            results['cleaned_entries'] = cleaned_entries
            
            logger.info(f"DNC scrub completed. Results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Full DNC scrub failed: {e}")
            raise
            
    async def _process_national_dnc(self, source_name: str) -> int:
        """
        Process National DNC Registry data.
        Downloads via FTP and processes the data.
        """
        logger.info("Processing National DNC Registry")
        
        try:
            # Connect to National DNC Registry FTP
            dnc_data = await self._download_national_dnc_ftp()
            
            # Process the downloaded data
            numbers_processed = 0
            for phone_number in dnc_data:
                await self._add_or_update_dnc_entry(
                    phone_number=phone_number,
                    registry_source='national',
                    state=None
                )
                numbers_processed += 1
                
            return numbers_processed
            
        except Exception as e:
            logger.error(f"Error processing National DNC: {e}")
            return 0
            
    async def _download_national_dnc_ftp(self) -> List[str]:
        """
        Download National DNC Registry data via FTP.
        Note: This is a simplified version - actual implementation would need
        proper FTP credentials and file format handling.
        """
        phone_numbers = []
        
        try:
            # Mock implementation - in production, use actual FTP download
            # ftp = ftplib.FTP('ftp.donotcall.gov')
            # ftp.login(settings.dnc_registry_username, settings.dnc_registry_password)
            
            # For demo purposes, return empty list
            # In production, process actual DNC files
            logger.info("National DNC FTP download simulated")
            return phone_numbers
            
        except Exception as e:
            logger.error(f"FTP download failed: {e}")
            return []
            
    async def _process_state_dnc(self, source_name: str) -> int:
        """
        Process state-specific DNC registries.
        """
        state_code = source_name.replace('state_', '').upper()
        logger.info(f"Processing {state_code} state DNC registry")
        
        try:
            # Get state registry URL
            state_config = DNC_REGISTRY_CONFIG['state_registries'].get(state_code)
            if not state_config:
                logger.warning(f"No configuration for state {state_code}")
                return 0
                
            # Download state DNC data
            dnc_data = await self._download_state_dnc(state_code, state_config)
            
            # Process the data
            numbers_processed = 0
            for phone_number in dnc_data:
                await self._add_or_update_dnc_entry(
                    phone_number=phone_number,
                    registry_source='state',
                    state=state_code
                )
                numbers_processed += 1
                
            return numbers_processed
            
        except Exception as e:
            logger.error(f"Error processing {state_code} DNC: {e}")
            return 0
            
    async def _download_state_dnc(self, state_code: str, registry_url: str) -> List[str]:
        """
        Download state-specific DNC data.
        Implementation varies by state.
        """
        phone_numbers = []
        
        try:
            async with httpx.AsyncClient() as client:
                # Texas DNC Registry
                if state_code == 'TX':
                    phone_numbers = await self._download_texas_dnc(client)
                # Florida DNC Registry  
                elif state_code == 'FL':
                    phone_numbers = await self._download_florida_dnc(client)
                # New York DNC Registry
                elif state_code == 'NY':
                    phone_numbers = await self._download_newyork_dnc(client)
                # California DNC Registry
                elif state_code == 'CA':
                    phone_numbers = await self._download_california_dnc(client)
                    
            return phone_numbers
            
        except Exception as e:
            logger.error(f"Error downloading {state_code} DNC: {e}")
            return []
            
    async def _download_texas_dnc(self, client: httpx.AsyncClient) -> List[str]:
        """Download Texas No Call List"""
        try:
            # Texas provides CSV download
            response = await client.get(
                "https://www.texasnodncall.com/T_NCL_file.txt",
                timeout=30.0
            )
            
            if response.status_code == 200:
                # Process Texas format (simple text file)
                content = response.text
                phone_numbers = []
                
                for line in content.strip().split('\n'):
                    phone = self._normalize_phone_number(line.strip())
                    if phone:
                        phone_numbers.append(phone)
                        
                return phone_numbers
            else:
                logger.error(f"Texas DNC download failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Texas DNC download error: {e}")
            return []
            
    async def _download_florida_dnc(self, client: httpx.AsyncClient) -> List[str]:
        """Download Florida No Call List"""
        try:
            # Florida provides ZIP file download
            response = await client.get(
                "https://www.floridanodncall.com/dnc_download.zip",
                timeout=60.0
            )
            
            if response.status_code == 200:
                # Extract ZIP file
                zip_content = io.BytesIO(response.content)
                phone_numbers = []
                
                with zipfile.ZipFile(zip_content, 'r') as zip_file:
                    for filename in zip_file.namelist():
                        if filename.endswith('.txt') or filename.endswith('.csv'):
                            with zip_file.open(filename) as file:
                                content = file.read().decode('utf-8')
                                for line in content.strip().split('\n'):
                                    phone = self._normalize_phone_number(line.strip())
                                    if phone:
                                        phone_numbers.append(phone)
                                        
                return phone_numbers
            else:
                logger.error(f"Florida DNC download failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Florida DNC download error: {e}")
            return []
            
    async def _download_newyork_dnc(self, client: httpx.AsyncClient) -> List[str]:
        """Download New York Do Not Call List"""
        # New York requires special handling - often requires registration
        logger.info("NY DNC download - requires special registration")
        return []
        
    async def _download_california_dnc(self, client: httpx.AsyncClient) -> List[str]:
        """Download California Do Not Call List"""
        # California has specific requirements
        logger.info("CA DNC download - requires specific compliance")
        return []
        
    async def _process_company_dnc(self, source_name: str) -> int:
        """
        Process company-specific suppression lists.
        """
        logger.info("Processing company suppression list")
        
        try:
            # Load company suppression list from file or database
            company_suppression_file = self.temp_dir / "company_suppression.csv"
            
            if not company_suppression_file.exists():
                logger.info("No company suppression file found")
                return 0
                
            # Process company suppression list
            numbers_processed = 0
            with open(company_suppression_file, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                
                for row in reader:
                    if len(row) >= 1:
                        phone = self._normalize_phone_number(row[0])
                        if phone:
                            await self._add_or_update_dnc_entry(
                                phone_number=phone,
                                registry_source='company',
                                state=None
                            )
                            numbers_processed += 1
                            
            return numbers_processed
            
        except Exception as e:
            logger.error(f"Error processing company DNC: {e}")
            return 0
            
    def _normalize_phone_number(self, phone: str) -> Optional[str]:
        """
        Normalize phone number to standard format.
        Returns None if invalid.
        """
        if not phone:
            return None
            
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Must be 10 or 11 digits
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        else:
            return None
            
    async def _add_or_update_dnc_entry(self, phone_number: str, registry_source: str, state: Optional[str] = None):
        """
        Add or update DNC registry entry.
        """
        try:
            # Check if entry exists
            stmt = select(DNCRegistry).where(DNCRegistry.phone_number == phone_number)
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing entry
                existing.registry_source = registry_source
                existing.state = state
                existing.last_updated = datetime.utcnow()
                existing.is_active = True
            else:
                # Create new entry
                new_entry = DNCRegistry(
                    phone_number=phone_number,
                    registry_source=registry_source,
                    state=state,
                    is_active=True,
                    registered_date=datetime.utcnow()
                )
                self.session.add(new_entry)
                
            await self.session.commit()
            
        except Exception as e:
            logger.error(f"Error adding/updating DNC entry {phone_number}: {e}")
            await self.session.rollback()
            
    async def _update_lead_dnc_status(self) -> int:
        """
        Update lead DNC status based on registry.
        """
        try:
            # Get all leads that might be on DNC
            stmt = select(Lead).where(Lead.dnc_status == False)
            result = await self.session.execute(stmt)
            leads = result.scalars().all()
            
            dnc_updated = 0
            
            for lead in leads:
                # Check if lead phone is in DNC registry
                dnc_stmt = select(DNCRegistry).where(
                    DNCRegistry.phone_number == lead.phone,
                    DNCRegistry.is_active == True
                )
                dnc_result = await self.session.execute(dnc_stmt)
                dnc_entry = dnc_result.scalar_one_or_none()
                
                if dnc_entry:
                    # Update lead DNC status
                    lead.dnc_status = True
                    lead.dnc_date = datetime.utcnow()
                    lead.status = LeadStatus.DNC
                    dnc_updated += 1
                    
            await self.session.commit()
            logger.info(f"Updated {dnc_updated} leads with DNC status")
            return dnc_updated
            
        except Exception as e:
            logger.error(f"Error updating lead DNC status: {e}")
            await self.session.rollback()
            return 0
            
    async def _cleanup_old_dnc_entries(self) -> int:
        """
        Clean up old DNC entries (older than max_age_days).
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=DNC_REGISTRY_CONFIG['max_age_days'])
            
            stmt = select(DNCRegistry).where(DNCRegistry.last_updated < cutoff_date)
            result = await self.session.execute(stmt)
            old_entries = result.scalars().all()
            
            cleaned_count = 0
            for entry in old_entries:
                entry.is_active = False
                cleaned_count += 1
                
            await self.session.commit()
            logger.info(f"Cleaned {cleaned_count} old DNC entries")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning old DNC entries: {e}")
            await self.session.rollback()
            return 0
            
    async def check_phone_dnc_status(self, phone_number: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a phone number is on any DNC registry.
        Returns (is_dnc, source).
        """
        try:
            normalized_phone = self._normalize_phone_number(phone_number)
            if not normalized_phone:
                return False, None
                
            stmt = select(DNCRegistry).where(
                DNCRegistry.phone_number == normalized_phone,
                DNCRegistry.is_active == True
            )
            result = await self.session.execute(stmt)
            dnc_entry = result.scalar_one_or_none()
            
            if dnc_entry:
                return True, dnc_entry.registry_source
            else:
                return False, None
                
        except Exception as e:
            logger.error(f"Error checking DNC status for {phone_number}: {e}")
            return False, None
            
    async def scrub_lead_list(self, lead_ids: List[str]) -> Dict[str, int]:
        """
        Scrub a specific list of leads against DNC registry.
        """
        results = {
            'total_leads': len(lead_ids),
            'dnc_leads': 0,
            'clean_leads': 0
        }
        
        try:
            for lead_id in lead_ids:
                stmt = select(Lead).where(Lead.id == lead_id)
                result = await self.session.execute(stmt)
                lead = result.scalar_one_or_none()
                
                if lead:
                    is_dnc, source = await self.check_phone_dnc_status(lead.phone)
                    
                    if is_dnc:
                        lead.dnc_status = True
                        lead.dnc_date = datetime.utcnow()
                        lead.status = LeadStatus.DNC
                        results['dnc_leads'] += 1
                    else:
                        results['clean_leads'] += 1
                        
            await self.session.commit()
            return results
            
        except Exception as e:
            logger.error(f"Error scrubbing lead list: {e}")
            await self.session.rollback()
            return results
            
    async def add_company_suppression_numbers(self, phone_numbers: List[str]) -> int:
        """
        Add phone numbers to company suppression list.
        """
        added_count = 0
        
        try:
            for phone in phone_numbers:
                normalized_phone = self._normalize_phone_number(phone)
                if normalized_phone:
                    await self._add_or_update_dnc_entry(
                        phone_number=normalized_phone,
                        registry_source='company',
                        state=None
                    )
                    added_count += 1
                    
            logger.info(f"Added {added_count} numbers to company suppression list")
            return added_count
            
        except Exception as e:
            logger.error(f"Error adding company suppression numbers: {e}")
            return 0
            
# Async context manager for DNC scrubbing
async def get_dnc_scrubbing_service():
    """Get DNC scrubbing service with proper session management."""
    async with DNCScrubbingService() as service:
        yield service 