"""
Lease Digitizer - Document Loader Utility

Utility functions for loading and preprocessing documents from various
sources. Handles file system operations, batch loading, and document
validation.

Key Features:
- Batch document loading
- File validation and filtering
- Document preprocessing pipeline
- Support for multiple file formats
"""

from pathlib import Path
from typing import Iterator, Optional, Union

from src.config import get_settings
from src.tools.pdf_parser import ParsedDocument, PDFParserTool


class DocumentLoader:
    """
    Utility for loading documents from file system.
    
    Handles batch loading, validation, and preprocessing of documents.
    
    Example:
        >>> loader = DocumentLoader()
        >>> documents = loader.load_directory("path/to/leases")
        >>> for doc in documents:
        ...     print(f"Loaded: {doc.metadata.filename}")
    """
    
    def __init__(
        self,
        supported_extensions: Optional[list[str]] = None,
        max_file_size_mb: Optional[int] = None,
    ) -> None:
        """
        Initialize the document loader.
        
        Args:
            supported_extensions: List of supported file extensions
            max_file_size_mb: Maximum file size in MB
        """
        settings = get_settings()
        self.supported_extensions = supported_extensions or settings.supported_extensions
        self.max_file_size_bytes = (
            (max_file_size_mb or settings.max_document_size_mb) * 1024 * 1024
        )
        
        # Initialize tools
        self._pdf_parser = PDFParserTool()
    
    def validate_file(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """
        Validate a file for processing.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        if not file_path.is_file():
            return False, f"Not a file: {file_path}"
        
        extension = file_path.suffix.lower().lstrip(".")
        if extension not in self.supported_extensions:
            return False, f"Unsupported extension: {extension}"
        
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size_bytes:
            return False, f"File too large: {file_size / 1024 / 1024:.2f} MB"
        
        return True, None
    
    def load_file(self, file_path: Union[str, Path]) -> ParsedDocument:
        """
        Load and parse a single document.
        
        Args:
            file_path: Path to the document
            
        Returns:
            ParsedDocument with extracted content
            
        Raises:
            ValueError: If file is invalid or unsupported
        """
        path = Path(file_path)
        is_valid, error = self.validate_file(path)
        
        if not is_valid:
            raise ValueError(error)
        
        extension = path.suffix.lower().lstrip(".")
        
        if extension == "pdf":
            return self._pdf_parser.parse(path)
        else:
            # TODO: Add support for other file types
            raise NotImplementedError(f"Loading {extension} files not yet implemented")
    
    def load_directory(
        self,
        directory_path: Union[str, Path],
        recursive: bool = False,
    ) -> Iterator[tuple[Path, ParsedDocument | Exception]]:
        """
        Load all documents from a directory.
        
        Args:
            directory_path: Path to directory
            recursive: Whether to search subdirectories
            
        Yields:
            Tuples of (file_path, ParsedDocument or Exception)
        """
        dir_path = Path(directory_path)
        
        if not dir_path.exists() or not dir_path.is_dir():
            raise ValueError(f"Invalid directory: {dir_path}")
        
        pattern = "**/*" if recursive else "*"
        
        for file_path in dir_path.glob(pattern):
            if not file_path.is_file():
                continue
            
            extension = file_path.suffix.lower().lstrip(".")
            if extension not in self.supported_extensions:
                continue
            
            try:
                document = self.load_file(file_path)
                yield file_path, document
            except Exception as e:
                yield file_path, e
    
    def get_file_list(
        self,
        directory_path: Union[str, Path],
        recursive: bool = False,
    ) -> list[Path]:
        """
        Get list of loadable files in a directory.
        
        Args:
            directory_path: Path to directory
            recursive: Whether to search subdirectories
            
        Returns:
            List of valid file paths
        """
        dir_path = Path(directory_path)
        files = []
        
        pattern = "**/*" if recursive else "*"
        
        for file_path in dir_path.glob(pattern):
            if not file_path.is_file():
                continue
            
            is_valid, _ = self.validate_file(file_path)
            if is_valid:
                files.append(file_path)
        
        return sorted(files)


# TODO: Add async loading support
# TODO: Add progress tracking for batch operations
# TODO: Add document caching
# TODO: Add support for cloud storage (S3, GCS, Azure Blob)
# TODO: Add document deduplication
