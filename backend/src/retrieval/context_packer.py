"""
Context Packer

Packs retrieved chunks into LLM context with smart truncation.
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ContextPacker:
    """
    Pack code chunks into LLM context within token limits.
    """
    
    def __init__(
        self,
        max_tokens: int = 70000,
        system_reserved: int = 3000,
        output_reserved: int = 8192
    ):
        """
        Initialize context packer.
        
        Args:
            max_tokens: Maximum total tokens
            system_reserved: Tokens reserved for system prompt
            output_reserved: Tokens reserved for output
        """
        self.max_tokens = max_tokens
        self.system_reserved = system_reserved
        self.output_reserved = output_reserved
        
        self.available_tokens = max_tokens - system_reserved - output_reserved
        
        logger.info(f"Context packer initialized: {self.available_tokens} tokens available")
    
    def pack(
        self,
        chunks: List[Dict[str, Any]],
        query: str,
        prioritize_by_score: bool = True
    ) -> Dict[str, Any]:
        """
        Pack chunks into context.
        
        Args:
            chunks: Retrieved chunks with metadata
            query: User query
            prioritize_by_score: Whether to prioritize by relevance score
        
        Returns:
            Packed context dictionary
        """
        # Sort chunks by score if requested
        if prioritize_by_score:
            chunks = sorted(chunks, key=lambda x: x.get('hybrid_score', x.get('score', 0)), reverse=True)
        
        packed_chunks = []
        total_tokens = 0
        
        # Reserve tokens for query
        query_tokens = self._estimate_tokens(query)
        total_tokens += query_tokens
        
        # Pack chunks until we hit limit
        for chunk in chunks:
            content = chunk.get('content', '')
            chunk_tokens = chunk.get('token_count', self._estimate_tokens(content))
            
            if total_tokens + chunk_tokens > self.available_tokens:
                # Try to fit truncated version
                remaining = self.available_tokens - total_tokens
                
                if remaining > 50:  # Only if we have reasonable space
                    truncated = self._truncate_to_tokens(content, remaining)
                    packed_chunks.append({
                        **chunk,
                        'content': truncated,
                        'truncated': True,
                        'original_tokens': chunk_tokens,
                        'packed_tokens': remaining
                    })
                    total_tokens += remaining
                
                break
            
            packed_chunks.append({
                **chunk,
                'truncated': False,
                'packed_tokens': chunk_tokens
            })
            
            total_tokens += chunk_tokens
        
        logger.info(f"Packed {len(packed_chunks)}/{len(chunks)} chunks ({total_tokens} tokens)")
        
        return {
            'chunks': packed_chunks,
            'total_chunks': len(packed_chunks),
            'total_tokens': total_tokens,
            'truncated_count': sum(1 for c in packed_chunks if c.get('truncated', False))
        }
    
    def build_prompt(
        self,
        packed_context: Dict[str, Any],
        query: str,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Build final prompt with packed context.
        
        Args:
            packed_context: Packed context from pack()
            query: User query
            system_instruction: Optional system instruction
        
        Returns:
            Complete prompt string
        """
        prompt_parts = []
        
        # System instruction
        if system_instruction:
            prompt_parts.append(system_instruction)
            prompt_parts.append("\n\n")
        
        # Context
        prompt_parts.append("# Relevant Code Context\n\n")
        
        for i, chunk in enumerate(packed_context['chunks'], 1):
            file_path = chunk.get('file_path', 'unknown')
            start_line = chunk.get('start_line', 0)
            end_line = chunk.get('end_line', 0)
            content = chunk.get('content', '')
            
            prompt_parts.append(f"## Chunk {i}: {file_path} (lines {start_line}-{end_line})\n\n")
            prompt_parts.append(f"```{chunk.get('language', '')}\\n{content}\\n```\n\n")
        
        # Query
        prompt_parts.append(f"# User Query\n\n{query}\n\n")
        
        # Instructions
        prompt_parts.append("# Instructions\n\n")
        prompt_parts.append("Based on the code context above, please provide a detailed response to the user's query.\n")
        
        return ''.join(prompt_parts)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough: 1 token ≈ 4 characters for code
        return len(text) // 4
    
    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to approximately max_tokens."""
        # Rough: keep max_tokens * 4 characters
        max_chars = max_tokens * 4
        
        if len(text) <= max_chars:
            return text
        
        return text[:max_chars] + "\n... [truncated]"
    
    def pack_with_health(
        self,
        chunks: List[Dict[str, Any]],
        query: str,
        health_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Pack chunks considering code health scores.
        
        Higher health = higher priority for inclusion.
        """
        # Boost scores based on health
        for chunk in chunks:
            file_path = chunk.get('file_path', '')
            health = health_scores.get(file_path, 50.0) / 100.0
            
            base_score = chunk.get('hybrid_score', chunk.get('score', 0))
            chunk['adjusted_score'] = base_score * (0.8 + 0.2 * health)
        
        # Sort by adjusted score
        chunks_sorted = sorted(chunks, key=lambda x: x.get('adjusted_score', 0), reverse=True)
        
        return self.pack(chunks_sorted, query, prioritize_by_score=False)


def main():
    """CLI entry point."""
    # Test data
    chunks = [
        {
            'file_path': 'test.py',
            'start_line': 1,
            'end_line': 20,
            'content': 'def test():\n    pass\n' * 10,
            'language': 'python',
            'score': 0.9
        },
        {
            'file_path': 'test2.py',
            'start_line': 30,
            'end_line': 50,
            'content': 'class Test:\n    pass\n' * 10,
            'language': 'python',
            'score': 0.8
        }
    ]
    
    packer = ContextPacker(max_tokens=1000)
    
    packed = packer.pack(chunks, "What does this code do?")
    
    print(f"\n📦 Context Packing Results:")
    print(f"  Total chunks: {packed['total_chunks']}")
    print(f"  Total tokens: {packed['total_tokens']}")
    print(f"  Truncated: {packed['truncated_count']}")
    
    prompt = packer.build_prompt(packed, "What does this code do?")
    
    print(f"\n📝 Generated Prompt ({len(prompt)} chars):")
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)


if __name__ == "__main__":
    main()
