"""
UAE Official Sources Parser

Parses the official-sources.yaml whitelist and applies verification rules.
Official UAE sources are treated as authoritative (single source of truth).
"""

import yaml
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class OfficialSource:
    name: str
    platform: str
    handle: str
    source_type: str
    credibility: int
    priority: str
    
    @property
    def is_single_source_trusted(self) -> bool:
        """Whether this source type is trusted as single source"""
        return self.source_type in [
            'ruler',
            'federal_government', 
            'state_media',
            'civil_defense',
            'emergency_management',
            'police'
        ]

class UAEOfficialSources:
    """Manages official UAE government and authoritative sources"""
    
    def __init__(self, config_path: str = "config/official-sources.yaml"):
        self.sources: List[OfficialSource] = []
        self.rules: Dict = {}
        self.priority_levels: Dict = {}
        self._load_config(config_path)
    
    def _load_config(self, path: str):
        """Load official sources configuration"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Parse sources
            for src in config.get('sources', []):
                self.sources.append(OfficialSource(
                    name=src['name'],
                    platform=src['platform'],
                    handle=src['handle'].lower().strip(),
                    source_type=src['type'],
                    credibility=src['credibility'],
                    priority=src['priority']
                ))
            
            # Parse rules
            self.rules = config.get('rules', {})
            self.priority_levels = config.get('priority', {})
            
        except Exception as e:
            print(f"Warning: Could not load official sources config: {e}")
            # Create default empty config
            self.sources = []
            self.rules = {}
    
    def is_official_source(self, handle: str, platform: str = "twitter") -> bool:
        """Check if a handle is an official UAE source"""
        handle_clean = handle.lower().strip()
        for source in self.sources:
            if source.handle == handle_clean and source.platform == platform:
                return True
        return False
    
    def get_source_info(self, handle: str, platform: str = "twitter") -> Optional[OfficialSource]:
        """Get official source information"""
        handle_clean = handle.lower().strip()
        for source in self.sources:
            if source.handle == handle_clean and source.platform == platform:
                return source
        return None
    
    def get_trusted_sources(self) -> List[OfficialSource]:
        """Get all single-source-trusted official sources"""
        return [s for s in self.sources if s.is_single_source_trusted]
    
    def get_sources_by_type(self, source_type: str) -> List[OfficialSource]:
        """Get all sources of a specific type"""
        return [s for s in self.sources if s.source_type == source_type]
    
    def get_priority_sources(self, priority: str) -> List[OfficialSource]:
        """Get sources by priority level (immediate, high, medium, low)"""
        return [s for s in self.sources if s.priority == priority]
    
    def get_all_handles(self, platform: str = "twitter") -> List[str]:
        """Get list of all official handles for monitoring"""
        return [s.handle for s in self.sources if s.platform == platform]
    
    def calculate_source_weight(self, handle: str, platform: str = "twitter") -> int:
        """Calculate verification weight for a source"""
        source = self.get_source_info(handle, platform)
        if not source:
            return 0
        
        # Official sources get massive weight boost
        if source.is_single_source_trusted:
            return source.credibility * 2  # 200 points for trusted official sources
        
        return source.credibility
    
    def is_single_source_sufficient(self, handle: str, platform: str = "twitter") -> bool:
        """
        Check if this source is sufficient as single source of truth.
        Rulers, government, civil defense = immediate trust
        """
        source = self.get_source_info(handle, platform)
        if not source:
            return False
        
        # Single source trusted types
        trusted_types = self.rules.get('single_source_trusted', [])
        for rule in trusted_types:
            if source.source_type == rule.get('type'):
                if source.credibility >= rule.get('min_credibility', 0):
                    return True
        
        return False
    
    def get_verification_requirements(self, handle: str, platform: str = "twitter") -> Dict:
        """Get verification requirements for a specific source"""
        source = self.get_source_info(handle, platform)
        
        if not source:
            # Unknown source - require multiple sources
            return {
                'requires_multiple': True,
                'min_sources': 3,
                'is_official': False,
                'weight': 0
            }
        
        # Check if single source sufficient
        if self.is_single_source_sufficient(handle, platform):
            return {
                'requires_multiple': False,
                'min_sources': 1,
                'is_official': True,
                'weight': self.calculate_source_weight(handle, platform),
                'source_type': source.source_type,
                'priority': source.priority
            }
        
        # Check rules for this type
        multiple_rules = self.rules.get('require_multiple', [])
        for rule in multiple_rules:
            if source.source_type == rule.get('type'):
                return {
                    'requires_multiple': True,
                    'min_sources': rule.get('min_sources', 2),
                    'is_official': True,
                    'weight': self.calculate_source_weight(handle, platform),
                    'source_type': source.source_type,
                    'priority': source.priority
                }
        
        # Default for known official sources
        return {
            'requires_multiple': True,
            'min_sources': 2,
            'is_official': True,
            'weight': source.credibility,
            'source_type': source.source_type,
            'priority': source.priority
        }
    
    def get_all_rulers(self) -> List[OfficialSource]:
        """Get all UAE ruler accounts"""
        return self.get_sources_by_type('ruler')
    
    def get_all_civil_defense(self) -> List[OfficialSource]:
        """Get all civil defense accounts"""
        return self.get_sources_by_type('civil_defense')
    
    def get_all_police(self) -> List[OfficialSource]:
        """Get all police accounts"""
        return self.get_sources_by_type('police')
    
    def get_emergency_sources(self) -> List[OfficialSource]:
        """Get all emergency/crisis management sources"""
        return [
            *self.get_sources_by_type('civil_defense'),
            *self.get_sources_by_type('emergency_management'),
            *self.get_sources_by_type('police')
        ]

# Singleton instance for global use
_official_sources = None

def get_uae_official_sources() -> UAEOfficialSources:
    """Get singleton instance of UAE official sources"""
    global _official_sources
    if _official_sources is None:
        _official_sources = UAEOfficialSources()
    return _official_sources

# Example usage
if __name__ == "__main__":
    sources = get_uae_official_sources()
    
    print("=== UAE Official Sources ===\n")
    
    print("Rulers (Single Source of Truth):")
    for ruler in sources.get_all_rulers():
        print(f"  - {ruler.name}: {ruler.handle}")
    
    print("\nCivil Defense (Single Source of Truth):")
    for cd in sources.get_all_civil_defense():
        print(f"  - {cd.name}: {cd.handle}")
    
    print("\nPolice (Single Source of Truth):")
    for police in sources.get_all_police():
        print(f"  - {police.name}: {police.handle}")
    
    # Test verification
    print("\n=== Verification Tests ===")
    test_handles = [
        "@uae_cd",           # Civil defense - should be single source
        "@random_user",      # Unknown - requires multiple
        "@hhshkmohd",        # Ruler - single source
        "@gulf_news",        # Media - requires multiple
    ]
    
    for handle in test_handles:
        req = sources.get_verification_requirements(handle)
        needs = "single source" if not req['requires_multiple'] else f"{req['min_sources']}+ sources"
        official = "✓ OFFICIAL" if req['is_official'] else "✗ unofficial"
        print(f"\n{handle}:")
        print(f"  Official: {official}")
        print(f"  Requires: {needs}")
        print(f"  Weight: {req['weight']}")
