"""
Configuration Management

Loads and manages all application settings from environment variables.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    # Target Repository
    target_repo_path: str = Field(default="", env="TARGET_REPO_PATH")
    
    # LLM Configuration
    llm_model_type: str = Field(default="gemini-2.0-flash-exp", env="LLM_MODEL_TYPE")
    llm_fallback_model_type: str = Field(default="gemini-1.5-pro", env="LLM_FALLBACK_MODEL_TYPE")
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    
    # Embedding Model
    embedding_model_type: str = Field(default="bge-m3", env="EMBEDDING_MODEL_TYPE")
    embedding_model_path: str = Field(default="./models/bge-m3", env="EMBEDDING_MODEL_PATH")
    use_local_embeddings: bool = Field(default=True, env="USE_LOCAL_EMBEDDINGS")
    
    # Token Limits
    max_tokens_per_request: int = Field(default=70000, env="MAX_TOKENS_PER_REQUEST")
    system_prompt_reserved_tokens: int = Field(default=3000, env="SYSTEM_PROMPT_RESERVED_TOKENS")
    max_output_tokens: int = Field(default=8192, env="MAX_OUTPUT_TOKENS")
    
    # Rate Limiting
    rate_limit_req_per_min: int = Field(default=50, env="RATE_LIMIT_REQ_PER_MIN")
    rate_limit_tokens_per_min: int = Field(default=2000000, env="RATE_LIMIT_TOKENS_PER_MIN")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Vector Database (FAISS)
    vector_db_path: str = Field(default="./data/vector_db", env="VECTOR_DB_PATH")
    
    # Graph Database (Neo4j)
    neo4j_url: str = Field(default="bolt://localhost:7687", env="NEO4J_URL")
    neo4j_username: str = Field(default="neo4j", env="NEO4J_USERNAME")
    neo4j_password: str = Field(default="changeme", env="NEO4J_PASSWORD")
    
    # Memory Database (SQLite)
    memory_db_path: str = Field(default="./data/memory.db", env="MEMORY_DB_PATH")
    code_health_db_path: str = Field(default="./data/code_health.db", env="CODE_HEALTH_DB_PATH")
    
    # Indexing Settings
    chunk_size: int = Field(default=400, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=70, env="CHUNK_OVERLAP")
    generate_summaries: bool = Field(default=True, env="GENERATE_SUMMARIES")
    
    # Retrieval Settings
    semantic_search_top_k: int = Field(default=50, env="SEMANTIC_SEARCH_TOP_K")
    enable_graph_expansion: bool = Field(default=True, env="ENABLE_GRAPH_EXPANSION")
    enable_error_path_retrieval: bool = Field(default=True, env="ENABLE_ERROR_PATH_RETRIEVAL")
    use_code_health_ranking: bool = Field(default=True, env="USE_CODE_HEALTH_RANKING")
    
    # Advanced Features
    enable_offline_mode: bool = Field(default=False, env="ENABLE_OFFLINE_MODE")
    enable_llm_cache: bool = Field(default=True, env="ENABLE_LLM_CACHE")
    llm_cache_ttl: int = Field(default=86400, env="LLM_CACHE_TTL")  # 24 hours
    enable_recovery: bool = Field(default=True, env="ENABLE_RECOVERY")
    
    # Debugging
    enable_tier_escalation: bool = Field(default=True, env="ENABLE_TIER_ESCALATION")
    enable_retry_tree: bool = Field(default=True, env="ENABLE_RETRY_TREE")
    max_retry_attempts: int = Field(default=3, env="MAX_RETRY_ATTEMPTS")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    enable_cors: bool = Field(default=True, env="ENABLE_CORS")
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:3001", env="CORS_ORIGINS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="./logs/vibe-agent.log", env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            Path(self.vector_db_path).parent,
            Path(self.memory_db_path).parent,
            Path(self.code_health_db_path).parent,
            Path(self.log_file).parent,
            "data/sandbox",
            "data/index",
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings instance
    """
    settings = Settings()
    settings.ensure_directories()
    return settings
