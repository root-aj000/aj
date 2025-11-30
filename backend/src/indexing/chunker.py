"""
Code Chunker - Split source code into token-aware overlapping chunks

Chunks respect function/class boundaries and maintain context
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import hashlib
import re


@dataclass
class Chunk:
    """Represents a code chunk."""
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    token_count: int
    language: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CodeChunker:
    """
    Split source code into overlapping chunks with token-aware boundaries.
    """
    
    def __init__(
        self,
        chunk_size: int = 400,
        chunk_overlap: int = 70,
        respect_boundaries: bool = True
    ):
        """
        Initialize the code chunker.
        
        Args:
            chunk_size: Target chunk size in tokens
            chunk_overlap: Number of overlapping tokens between chunks
            respect_boundaries: Whether to respect function/class boundaries
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.respect_boundaries = respect_boundaries
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Uses simple word-based estimation (rough approximation).
        
        Args:
            text: Text to estimate
        
        Returns:
            Estimated token count
        """
        # Simple estimation: split by whitespace and punctuation
        # Roughly: 1 token ≈ 0.75 words for code
        words = len(re.findall(r'\w+', text))
        return int(words * 1.3)  # Code tends to have more tokens per word
    
    def generate_chunk_id(self, file_path: str, start_line: int, end_line: int) -> str:
        """
        Generate a unique chunk ID.
        
        Args:
            file_path: Path to source file
            start_line: Starting line number
            end_line: Ending line number
        
        Returns:
            SHA1 hash of filepath + line span
        """
        content = f"{file_path}:{start_line}-{end_line}"
        return hashlib.sha1(content.encode()).hexdigest()
    
    def chunk_file(
        self,
        file_path: str,
        content: str,
        language: str,
        functions: Optional[List[Dict[str, Any]]] = None
    ) -> List[Chunk]:
        """
        Chunk a file into overlapping segments.
        
        Args:
            file_path: Path to source file
            content: File content
            language: Programming language
            functions: Optional list of function boundaries
        
        Returns:
            List of Chunk objects
        """
        lines = content.splitlines()
        chunks: List[Chunk] = []
        
        if self.respect_boundaries and functions:
            # Chunk respecting function boundaries
            chunks = self._chunk_with_boundaries(file_path, lines, language, functions)
        else:
            # Simple overlapping chunks
            chunks = self._chunk_simple(file_path, lines, language)
        
        return chunks
    
    def _chunk_simple(
        self,
        file_path: str,
        lines: List[str],
        language: str
    ) -> List[Chunk]:
        """Create simple overlapping chunks."""
        chunks: List[Chunk] = []
        total_lines = len(lines)
        
        start_line = 0
        
        while start_line < total_lines:
            # Determine end line based on token count
            end_line = start_line
            current_tokens = 0
            
            while end_line < total_lines and current_tokens < self.chunk_size:
                line_tokens = self.estimate_tokens(lines[end_line])
                current_tokens += line_tokens
                end_line += 1
            
            # Create chunk
            chunk_lines = lines[start_line:end_line]
            chunk_content = '\n'.join(chunk_lines)
            
            chunk = Chunk(
                chunk_id=self.generate_chunk_id(file_path, start_line + 1, end_line),
                file_path=file_path,
                start_line=start_line + 1,  # 1-indexed
                end_line=end_line,
                content=chunk_content,
                token_count=self.estimate_tokens(chunk_content),
                language=language
            )
            
            chunks.append(chunk)
            
            # Move start position with overlap
            # Calculate overlap in lines
            overlap_tokens = 0
            overlap_lines = 0
            
            for i in range(end_line - 1, start_line - 1, -1):
                overlap_tokens += self.estimate_tokens(lines[i])
                overlap_lines += 1
                
                if overlap_tokens >= self.chunk_overlap:
                    break
            
            start_line = end_line - overlap_lines
            
            # Prevent infinite loop
            if start_line >= end_line:
                start_line = end_line
        
        return chunks
    
    def _chunk_with_boundaries(
        self,
        file_path: str,
        lines: List[str],
        language: str,
        functions: List[Dict[str, Any]]
    ) -> List[Chunk]:
        """
        Create chunks respecting function boundaries.
        
        Each function gets its own chunk if possible.
        Large functions are still split.
        """
        chunks: List[Chunk] = []
        
        # Sort functions by start line
        sorted_functions = sorted(functions, key=lambda f: f['start_line'])
        
        last_end = 0
        
        for func in sorted_functions:
            func_start = func['start_line'] - 1  # 0-indexed
            func_end = func['end_line']
            
            # Add gap between functions if it exists
            if last_end < func_start:
                gap_lines = lines[last_end:func_start]
                if gap_lines:
                    gap_content = '\n'.join(gap_lines)
                    gap_tokens = self.estimate_tokens(gap_content)
                    
                    if gap_tokens > 50:  # Only create chunk if substantial
                        chunk = Chunk(
                            chunk_id=self.generate_chunk_id(file_path, last_end + 1, func_start),
                            file_path=file_path,
                            start_line=last_end + 1,
                            end_line=func_start,
                            content=gap_content,
                            token_count=gap_tokens,
                            language=language
                        )
                        chunks.append(chunk)
            
            # Add function chunk
            func_lines = lines[func_start:func_end]
            func_content = '\n'.join(func_lines)
            func_tokens = self.estimate_tokens(func_content)
            
            # If function is too large, split it
            if func_tokens > self.chunk_size * 1.5:
                sub_chunks = self._chunk_simple(file_path, func_lines, language)
                chunks.extend(sub_chunks)
            else:
                chunk = Chunk(
                    chunk_id=self.generate_chunk_id(file_path, func_start + 1, func_end),
                    file_path=file_path,
                    start_line=func_start + 1,
                    end_line=func_end,
                    content=func_content,
                    token_count=func_tokens,
                    language=language
                )
                chunks.append(chunk)
            
            last_end = func_end
        
        # Add remaining content after last function
        if last_end < len(lines):
            remaining_lines = lines[last_end:]
            remaining_content = '\n'.join(remaining_lines)
            remaining_tokens = self.estimate_tokens(remaining_content)
            
            if remaining_tokens > 50:
                chunk = Chunk(
                    chunk_id=self.generate_chunk_id(file_path, last_end + 1, len(lines)),
                    file_path=file_path,
                    start_line=last_end + 1,
                    end_line=len(lines),
                    content=remaining_content,
                    token_count=remaining_tokens,
                    language=language
                )
                chunks.append(chunk)
        
        return chunks


def main():
    """CLI entry point for testing."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python chunker.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    chunker = CodeChunker(chunk_size=400, chunk_overlap=70)
    chunks = chunker.chunk_file(file_path, content, 'python')
    
    print(f"\n✅ Created {len(chunks)} chunks")
    print(f"\nChunk summary:")
    for i, chunk in enumerate(chunks, 1):
        print(f"  Chunk {i}: lines {chunk.start_line}-{chunk.end_line} ({chunk.token_count} tokens)")


if __name__ == "__main__":
    main()
