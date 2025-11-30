"""
Multi-file Patch Planner

Plans atomic multi-file changes considering dependencies and conflicts.
"""

from typing import List, Dict, Any, Set, Optional, Tuple
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    """Represents a change to a single file."""
    file_path: str
    original_content: str
    patched_content: str
    change_type: str  # 'modify', 'create', 'delete'
    dependencies: List[str]  # Other files this change depends on


@dataclass
class MultiFilePatch:
    """Represents a multi-file patch with dependencies."""
    patch_id: str
    description: str
    changes: List[FileChange]
    dependency_order: List[str]  # Order to apply changes
    conflicts: List[Dict[str, Any]]
    impact_analysis: Dict[str, Any]


class MultiFilePatchPlanner:
    """
    Plan atomic multi-file changes.
    
    Features:
    - Dependency resolution
    - Conflict detection
    - Impact prediction
    - Atomic application (all or nothing)
    """
    
    def __init__(self, neo4j_client=None, symbol_tracer=None):
        """
        Initialize planner.
        
        Args:
            neo4j_client: Neo4j client for dependency queries
            symbol_tracer: Symbol lineage tracer
        """
        self.neo4j_client = neo4j_client
        self.symbol_tracer = symbol_tracer
    
    def create_multi_file_patch(
        self,
        changes: List[Dict[str, Any]],
        description: str = ""
    ) -> MultiFilePatch:
        """
        Create a multi-file patch plan.
        
        Args:
            changes: List of file changes
            description: Patch description
        
        Returns:
            Multi-file patch plan
        """
        logger.info(f"Planning multi-file patch with {len(changes)} changes")
        
        # Convert to FileChange objects
        file_changes = [
            FileChange(
                file_path=c['file_path'],
                original_content=c.get('original_content', ''),
                patched_content=c['patched_content'],
                change_type=c.get('change_type', 'modify'),
                dependencies=c.get('dependencies', [])
            )
            for c in changes
        ]
        
        # Resolve dependency order
        dependency_order = self._resolve_dependencies(file_changes)
        
        # Detect conflicts
        conflicts = self._detect_conflicts(file_changes)
        
        # Analyze impact
        impact = self._analyze_impact(file_changes)
        
        patch = MultiFilePatch(
            patch_id=f"mfp_{hash(description)}",
            description=description,
            changes=file_changes,
            dependency_order=dependency_order,
            conflicts=conflicts,
            impact_analysis=impact
        )
        
        return patch
    
    def _resolve_dependencies(
        self,
        changes: List[FileChange]
    ) -> List[str]:
        """
        Resolve dependency order for applying changes.
        
        Uses topological sort.
        """
        # Build dependency graph
        graph: Dict[str, Set[str]] = {}
        in_degree: Dict[str, int] = {}
        
        for change in changes:
            graph[change.file_path] = set(change.dependencies)
            in_degree[change.file_path] = 0
        
        # Calculate in-degrees
        for file_path in graph:
            for dep in graph[file_path]:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # Topological sort (Kahn's algorithm)
        queue = [f for f in graph if in_degree[f] == 0]
        order = []
        
        while queue:
            current = queue.pop(0)
            order.append(current)
            
            for neighbor in graph.get(current, set()):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        
        # Check for cycles
        if len(order) != len(changes):
            logger.warning("Circular dependencies detected in patch")
        
        return order
    
    def _detect_conflicts(
        self,
        changes: List[FileChange]
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts between changes.
        
        Conflicts occur when:
        - Multiple changes to same file/lines
        - Symbol renames that clash
        - Incompatible type changes
        """
        conflicts = []
        
        # Group changes by file
        by_file: Dict[str, List[FileChange]] = {}
        for change in changes:
            if change.file_path not in by_file:
                by_file[change.file_path] = []
            by_file[change.file_path].append(change)
        
        # Check for multiple changes to same file
        for file_path, file_changes in by_file.items():
            if len(file_changes) > 1:
                conflicts.append({
                    'type': 'multiple_changes',
                    'file': file_path,
                    'count': len(file_changes),
                    'severity': 'high',
                    'message': f"Multiple changes to {file_path}",
                })
        
        # Check for symbol conflicts using symbol tracer
        if self.symbol_tracer:
            # Would check for rename conflicts, etc.
            pass
        
        return conflicts
    
    def _analyze_impact(
        self,
        changes: List[FileChange]
    ) -> Dict[str, Any]:
        """
        Analyze impact of multi-file patch.
        
        Returns:
            Impact analysis data
        """
        impact = {
            'total_files': len(changes),
            'total_additions': 0,
            'total_deletions': 0,
            'files_modified': 0,
            'files_created': 0,
            'files_deleted': 0,
            'risk_score': 0.0,
            'affected_modules': set(),
        }
        
        for change in changes:
            if change.change_type == 'modify':
                impact['files_modified'] += 1
            elif change.change_type == 'create':
                impact['files_created'] += 1
            elif change.change_type == 'delete':
                impact['files_deleted'] += 1
            
            # Calculate line changes
            original_lines = change.original_content.count('\n')
            patched_lines = change.patched_content.count('\n')
            
            if patched_lines > original_lines:
                impact['total_additions'] += patched_lines - original_lines
            else:
                impact['total_deletions'] += original_lines - patched_lines
            
            # Track modules
            module = str(Path(change.file_path).parent)
            impact['affected_modules'].add(module)
        
        # Calculate risk score (0-100)
        base_risk = len(changes) * 10  # More files = more risk
        conflict_risk = len(self._detect_conflicts(changes)) * 20
        impact['risk_score'] = min(100, base_risk + conflict_risk)
        
        # Convert set to list for JSON serialization
        impact['affected_modules'] = list(impact['affected_modules'])
        
        return impact
    
    def validate_patch(self, patch: MultiFilePatch) -> Dict[str, Any]:
        """
        Validate multi-file patch before application.
        
        Returns:
            Validation result
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'can_apply': True,
        }
        
        # Check for conflicts
        if patch.conflicts:
            result['warnings'].append(
                f"Found {len(patch.conflicts)} conflicts"
            )
            
            high_severity = [c for c in patch.conflicts if c['severity'] == 'high']
            if high_severity:
                result['valid'] = False
                result['can_apply'] = False
                result['errors'].append(
                    f"{len(high_severity)} high-severity conflicts must be resolved"
                )
        
        # Check dependency order
        if not patch.dependency_order:
            result['errors'].append("Could not resolve dependency order")
            result['valid'] = False
        
        # Check risk score
        if patch.impact_analysis['risk_score'] > 80:
            result['warnings'].append(
                f"High risk score: {patch.impact_analysis['risk_score']}"
            )
        
        return result
    
    def generate_preview(self, patch: MultiFilePatch) -> str:
        """
        Generate human-readable preview of multi-file patch.
        
        Returns:
            Preview text
        """
        lines = []
        lines.append(f"=== Multi-File Patch: {patch.description} ===\n")
        lines.append(f"Patch ID: {patch.patch_id}")
        lines.append(f"Total files: {patch.impact_analysis['total_files']}")
        lines.append(f"Risk score: {patch.impact_analysis['risk_score']}/100\n")
        
        lines.append("Changes:")
        for idx, change in enumerate(patch.changes, 1):
            lines.append(f"  {idx}. {change.change_type.upper()}: {change.file_path}")
            if change.dependencies:
                lines.append(f"     Dependencies: {', '.join(change.dependencies)}")
        
        if patch.conflicts:
            lines.append(f"\n⚠️  {len(patch.conflicts)} conflicts detected:")
            for conflict in patch.conflicts:
                lines.append(f"  - {conflict['message']}")
        
        lines.append(f"\nApplication order:")
        for idx, file_path in enumerate(patch.dependency_order, 1):
            lines.append(f"  {idx}. {file_path}")
        
        return '\n'.join(lines)


def main():
    """CLI entry point."""
    planner = MultiFilePatchPlanner()
    
    # Example multi-file patch
    changes = [
        {
            'file_path': 'models/user.py',
            'patched_content': '# Updated user model',
            'change_type': 'modify',
            'dependencies': [],
        },
        {
            'file_path': 'api/users.py',
            'patched_content': '# Updated API',
            'change_type': 'modify',
            'dependencies': ['models/user.py'],
        },
        {
            'file_path': 'tests/test_users.py',
            'patched_content': '# Updated tests',
            'change_type': 'modify',
            'dependencies': ['models/user.py', 'api/users.py'],
        },
    ]
    
    patch = planner.create_multi_file_patch(
        changes,
        description="Update user model and API"
    )
    
    print(planner.generate_preview(patch))
    
    validation = planner.validate_patch(patch)
    print(f"\nValidation: {'✅ PASS' if validation['valid'] else '❌ FAIL'}")


if __name__ == "__main__":
    main()
