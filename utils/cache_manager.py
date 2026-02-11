"""
Sistema de Cache Inteligente
Implementa cache distribuído com TTL e estratégias de invalidação.
"""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import hashlib

from config import DATA_DIR

logger = logging.getLogger(__name__)

class CacheManager:
    """Gerenciador de cache inteligente com múltiplas estratégias."""
    
    def __init__(self):
        self.cache_dir = DATA_DIR / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Configurações de TTL por tipo de dado
        self.ttl_config = {
            'api_primary': timedelta(hours=1),
            'api_secondary': timedelta(hours=6),
            'csv_fallback': timedelta(days=7),
            'converted_xlsx': timedelta(days=30),
            'processed_data': timedelta(hours=2),
            'health_check': timedelta(minutes=5),
            'metrics': timedelta(minutes=15)
        }
        
        # Estratégias de cache
        self.strategies = {
            'lru': self._lru_strategy,
            'fifo': self._fifo_strategy,
            'lfu': self._lfu_strategy
        }
        
        # Métricas do cache
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size_bytes': 0,
            'entries': 0
        }
        
        # Configuração de tamanho máximo
        self.max_cache_size_mb = 100  # 100MB
        self.max_entries = 1000
        
        # Cache em memória para acesso rápido
        self._memory_cache = {}
        self._memory_cache_keys = []
    
    def _get_cache_key(self, key: str, namespace: str = None) -> str:
        """Gera chave única para cache."""
        if namespace:
            key = f"{namespace}:{key}"
        
        # Usar hash para evitar problemas com caracteres especiais
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Retorna o caminho do arquivo de cache."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, cache_key: str, ttl: timedelta = None) -> bool:
        """Verifica se o cache ainda é válido."""
        cache_file = self._get_cache_file_path(cache_key)
        
        if not cache_file.exists():
            return False
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Verificar TTL
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            cache_ttl = ttl or self.ttl_config.get(cache_data.get('source_type', 'api_primary'), timedelta(hours=1))
            
            return datetime.now() - cached_at < cache_ttl
            
        except Exception as e:
            logger.error(f"Erro ao validar cache {cache_key}: {e}")
            return False
    
    def get(self, key: str, namespace: str = None, ttl: timedelta = None) -> Optional[Any]:
        """Recupera valor do cache."""
        cache_key = self._get_cache_key(key, namespace)
        
        # Verificar cache em memória primeiro
        if cache_key in self._memory_cache:
            self.metrics['hits'] += 1
            return self._memory_cache[cache_key]['data']
        
        # Verificar cache em disco
        cache_file = self._get_cache_file_path(cache_key)
        
        if not self._is_cache_valid(cache_key, ttl):
            self.metrics['misses'] += 1
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Carregar para cache em memória
            self._add_to_memory_cache(cache_key, cache_data['data'])
            
            self.metrics['hits'] += 1
            return cache_data['data']
            
        except Exception as e:
            logger.error(f"Erro ao ler cache {cache_key}: {e}")
            self.metrics['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, namespace: str = None, 
              source_type: str = 'api_primary', metadata: Dict = None) -> bool:
        """Salva valor no cache."""
        cache_key = self._get_cache_key(key, namespace)
        
        cache_data = {
            'key': key,
            'namespace': namespace,
            'source_type': source_type,
            'cached_at': datetime.now().isoformat(),
            'data': value,
            'metadata': metadata or {}
        }
        
        try:
            # Salvar em cache em memória
            self._add_to_memory_cache(cache_key, cache_data['data'])
            
            # Salvar em disco
            cache_file = self._get_cache_file_path(cache_key)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            # Limpar cache se necessário
            self._cleanup_if_needed()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar cache {cache_key}: {e}")
            return False
    
    def _add_to_memory_cache(self, cache_key: str, data: Any):
        """Adiciona ao cache em memória."""
        # Se já existe, remover da lista de chaves para reposicionar no final
        if cache_key in self._memory_cache:
            self._memory_cache_keys.remove(cache_key)
        
        # Adicionar ao cache e à lista
        self._memory_cache[cache_key] = {
            'data': data,
            'accessed_at': datetime.now()
        }
        self._memory_cache_keys.append(cache_key)
        
        # Manter limite de entradas
        if len(self._memory_cache_keys) > 100:  # Limite de 100 entradas em memória
            oldest_key = self._memory_cache_keys.pop(0)
            del self._memory_cache[oldest_key]
            self.metrics['evictions'] += 1
    
    def delete(self, key: str, namespace: str = None) -> bool:
        """Remove entrada do cache."""
        cache_key = self._get_cache_key(key, namespace)
        
        # Remover da memória
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]
            self._memory_cache_keys.remove(cache_key)
        
        # Remover do disco
        cache_file = self._get_cache_file_path(cache_key)
        if cache_file.exists():
            cache_file.unlink()
            return True
        
        return False
    
    def clear(self, namespace: str = None) -> int:
        """Limpa cache (namespace específico ou todo)."""
        cleared_count = 0
        
        if namespace:
            # Limpar namespace específico
            keys_to_remove = []
            for cache_key in self._memory_cache_keys:
                if cache_key.startswith(hashlib.md5(f"{namespace}:".encode()).hexdigest()):
                    keys_to_remove.append(cache_key)
            
            for cache_key in keys_to_remove:
                del self._memory_cache[cache_key]
                self._memory_cache_keys.remove(cache_key)
                cleared_count += 1
            
            # Limpar arquivos do namespace
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    if cache_data.get('namespace') == namespace:
                        cache_file.unlink()
                        cleared_count += 1
                        
                except:
                    continue
        else:
            # Limpar todo o cache
            self._memory_cache.clear()
            self._memory_cache_keys.clear()
            
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                cleared_count += 1
        
        # Resetar métricas
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size_bytes': 0,
            'entries': 0
        }
        
        logger.info(f"Cache limpo: {cleared_count} entradas removidas")
        return cleared_count
    
    def _cleanup_if_needed(self):
        """Limpa cache se necessário."""
        # Verificar tamanho em bytes
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        
        # Verificar número de entradas
        total_entries = len(list(self.cache_dir.glob("*.json")))
        
        # Limpar se exceder limites
        if total_size > self.max_cache_size_mb * 1024 * 1024 or total_entries > self.max_entries:
            self._evict_lru()
    
    def _evict_lru(self):
        """Remove entradas menos usadas recentemente (LRU)."""
        cache_files = []
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                cache_files.append({
                    'file': cache_file,
                    'accessed_at': cache_data.get('metadata', {}).get('accessed_at', cache_data['cached_at']),
                    'size': cache_file.stat().st_size
                })
            except:
                continue
        
        # Ordenar por último acesso
        cache_files.sort(key=lambda x: x['accessed_at'])
        
        # Remover até atingir limites
        target_size = self.max_cache_size_mb * 1024 * 1024 * 0.8  # 80% do máximo
        target_entries = self.max_entries * 0.8  # 80% do máximo
        
        current_size = sum(f['size'] for f in cache_files)
        current_entries = len(cache_files)
        
        removed_count = 0
        for cache_info in cache_files:
            if current_size <= target_size and current_entries <= target_entries:
                break
            
            cache_info['file'].unlink()
            current_size -= cache_info['size']
            current_entries -= 1
            removed_count += 1
        
        self.metrics['evictions'] += removed_count
        logger.info(f"Cache LRU eviction: {removed_count} entradas removidas")
    
    def get_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o cache."""
        cache_files = list(self.cache_dir.glob("*.json"))
        
        total_size = sum(f.stat().st_size for f in cache_files)
        
        # Análise por tipo de fonte
        source_stats = {}
        for cache_file in cache_files:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                source_type = cache_data.get('source_type', 'unknown')
                if source_type not in source_stats:
                    source_stats[source_type] = 0
                source_stats[source_type] += 1
                
            except:
                continue
        
        # Calcular hit rate
        total_requests = self.metrics['hits'] + self.metrics['misses']
        hit_rate = (self.metrics['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'timestamp': datetime.now().isoformat(),
            'entries': len(cache_files),
            'size_bytes': total_size,
            'size_mb': total_size / (1024 * 1024),
            'memory_entries': len(self._memory_cache_keys),
            'hit_rate': hit_rate,
            'hits': self.metrics['hits'],
            'misses': self.metrics['misses'],
            'evictions': self.metrics['evictions'],
            'source_stats': source_stats,
            'ttl_config': {k: str(v) for k, v in self.ttl_config.items()}
        }
    
    def get_expired_entries(self) -> List[Dict[str, Any]]:
        """Retorna entradas expiradas."""
        expired = []
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                cached_at = datetime.fromisoformat(cache_data['cached_at'])
                source_type = cache_data.get('source_type', 'api_primary')
                ttl = self.ttl_config.get(source_type, timedelta(hours=1))
                
                if datetime.now() - cached_at > ttl:
                    expired.append({
                        'file': cache_file.name,
                        'key': cache_data.get('key', 'unknown'),
                        'namespace': cache_data.get('namespace'),
                        'source_type': source_type,
                        'cached_at': cache_data['cached_at'],
                        'expired_since': str(datetime.now() - cached_at)
                    })
                    
            except:
                continue
        
        return expired
    
    def cleanup_expired(self) -> int:
        """Remove entradas expiradas."""
        expired_entries = self.get_expired_entries()
        removed_count = 0
        
        for entry in expired_entries:
            cache_file = self.cache_dir / entry['file']
            cache_file.unlink()
            removed_count += 1
        
        # Limpar cache em memória de entradas expiradas
        keys_to_remove = []
        for cache_key in self._memory_cache_keys:
            cache_data = self._memory_cache[cache_key]
            cached_at = cache_data.get('accessed_at', datetime.now())
            
            # Se não foi acessado recentemente, pode estar expirado
            if datetime.now() - cached_at > timedelta(hours=1):
                keys_to_remove.append(cache_key)
        
        for cache_key in keys_to_remove:
            del self._memory_cache[cache_key]
            self._memory_cache_keys.remove(cache_key)
            removed_count += 1
        
        logger.info(f"Cleanup expirado: {removed_count} entradas removidas")
        return removed_count

# Instância global do gerenciador de cache
cache_manager = CacheManager()
