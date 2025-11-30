"""
Manifest Generator - Combine all indexing results into a unified manifest

Aggregates file metadata, AST data, chunks, and summaries into a single structure.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from datetime import datetime
import logging

from walker import FileWalker, FileMetadata
from ast_parser import ASTParser
from chunker import CodeChunker, Chunk

logger = logging.getLogger(__name__)


class ManifestGenerator:
    """
    Generate comprehensive manifest from indexing results.
    """
    
    def __init__(
        self,
        walker: FileWalker,
        parser: ASTParser,
        chunker: CodeChunker
    ):
        """
        Initialize manifest generator.
        
        Args:
            walker: File walker instance
            parser: AST parser instance
            chunker: Code chunker instance
        """
        self.walker = walker
        self.parser = parser
        self.chunker = chunker
    
    def generate(
        self,
        include_ast: bool = False,
        include_chunks: bool = True
    ) -> Dict[str, Any]:
        """
        Generate complete manifest.
        
        Args:
            include_ast: Whether to include full AST data (large)
            include_chunks: Whether to include chunk data
        
        Returns:
            Complete manifest dictionary
        """
        logger.info("Starting manifest generation...")
        
        # Walk directory tree
        files = self.walker.walk()
        logger.info(f"Discovered {len(files)} files")
        
        # Process each file
        processed_files = []
        total_chunks = 0
        total_functions = 0
        total_classes = 0
        
        for file_meta in files:
            logger.debug(f"Processing {file_meta.relative_path}")
            
            file_data = {
                'path': file_meta.path,
                'relative_path': file_meta.relative_path,
                'size_bytes': file_meta.size_bytes,
                'modified_time': file_meta.modified_time,
                'language': file_meta.language,
            }
            
            # Parse AST
            try:
                ast_data = self.parser.parse_file(file_meta.path, file_meta.language)
                
                if ast_data:
                    # Extract functions and classes
                    functions = self.parser.extract_functions(ast_data)
                    classes = self.parser.extract_classes(ast_data)
                    
                    file_data['has_parse_errors'] = ast_data.get('has_errors', False)
                    file_data['functions'] = functions
                    file_data['classes'] = classes
                    file_data['function_count'] = len(functions)
                    file_data['class_count'] = len(classes)
                    
                    total_functions += len(functions)
                    total_classes += len(classes)
                    
                    # Include full AST if requested
                    if include_ast:
                        file_data['ast'] = ast_data.get('ast')
                    
                    # Generate chunks
                    if include_chunks:
                        with open(file_meta.path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        chunks = self.chunker.chunk_file(
                            file_meta.path,
                            content,
                            file_meta.language,
                            functions
                        )
                        
                        file_data['chunks'] = [chunk.to_dict() for chunk in chunks]
                        file_data['chunk_count'] = len(chunks)
                        total_chunks += len(chunks)
                else:
                    file_data['has_parse_errors'] = True
                    file_data['functions'] = []
                    file_data['classes'] = []
                    file_data['function_count'] = 0
                    file_data['class_count'] = 0
                    
            except Exception as e:
                logger.error(f"Error processing {file_meta.path}: {e}")
                file_data['processing_error'] = str(e)
            
            processed_files.append(file_data)
        
        # Build manifest
        manifest = {
            'metadata': {
                'root_path': str(self.walker.root_path),
                'generated_at': datetime.now().isoformat(),
                'version': '1.0.0',
            },
            'statistics': {
                'total_files': len(files),
                'total_functions': total_functions,
                'total_classes': total_classes,
                'total_chunks': total_chunks,
                'languages': self._count_by_language(files),
            },
            'files': processed_files,
        }
        
        logger.info("Manifest generation complete")
        logger.info(f"  Files: {len(files)}")
        logger.info(f"  Functions: {total_functions}")
        logger.info(f"  Classes: {total_classes}")
        logger.info(f"  Chunks: {total_chunks}")
        
        return manifest
    
    def _count_by_language(self, files: List[FileMetadata]) -> Dict[str, int]:
        """Count files by language."""
        counts: Dict[str, int] = {}
        for file in files:
            lang = file.language
            counts[lang] = counts.get(lang, 0) + 1
        return counts
    
    def save_manifest(self, manifest: Dict[str, Any], output_path: str):
        """
        Save manifest to JSON file.
        
        Args:
            manifest: Manifest dictionary
            output_path: Output file path
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Manifest saved to {output_path}")


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python manifest.py <repo_path> [output.json]")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "manifest.json"
    
    # Initialize components
    walker = FileWalker(repo_path)
    parser = ASTParser()
    chunker = CodeChunker(chunk_size=400, chunk_overlap=70)
    
    # Generate manifest
    generator = ManifestGenerator(walker, parser, chunker)
    manifest = generator.generate(include_ast=False, include_chunks=True)
    
    # Save to file
    generator.save_manifest(manifest, output_path)
    
    print(f"\n✅ Manifest generated successfully")
    print(f"📄 Saved to: {output_path}")


if __name__ == "__main__":
    main()
