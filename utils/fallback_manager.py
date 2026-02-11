"""
Sistema de Fallback Robusto para APIs e Dados
Implementa cache inteligente, retry com exponential backoff e múltiplas fontes de dados.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd
import requests
from pathlib import Path
import json
import time

from config import DATA_DIR, COD_IBGE, MUNICIPIO, UF

logger = logging.getLogger(__name__)

class FallbackManager:
    """Gerenciador de fallback robusto para APIs e dados."""
    
    def __init__(self):
        self.cache = {}
        self.cache_dir = DATA_DIR / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Configuração de TTL para diferentes fontes
        self.cache_ttl = {
            'api_primary': timedelta(hours=1),
            'api_secondary': timedelta(hours=6),
            'csv_fallback': timedelta(days=7),
            'converted_xlsx': timedelta(days=30)
        }
        
        # Configuração de fontes por prioridade
        self.fallback_sources = {
            'IBGE': ['api_primary', 'api_secondary', 'csv_fallback'],
            'CAGED': ['api_primary', 'csv_fallback'],
            'RAIS': ['api_primary', 'csv_fallback'],
            'SEFAZ_MG': ['api_primary', 'csv_fallback'],
            'DATASUS': ['api_primary', 'csv_fallback'],
            'INEP': ['api_primary', 'csv_fallback'],
            'IDSC': ['api_primary', 'csv_fallback'],
            'SEEG': ['api_primary', 'csv_fallback'],
            'SEBRAE': ['csv_fallback', 'converted_xlsx'],
            'MapBiomas': ['api_primary', 'csv_fallback', 'converted_xlsx']
        }
        
        # Configuração de URLs primárias e secundárias
        self.api_endpoints = {
            'IBGE': {
                'api_primary': 'https://servicodados.ibge.gov.br/api/v3/agregados/estatisticas',
                'api_secondary': 'https://servicodados.ibge.gov.br/api/v3/agregados'
            },
            'CAGED': {
                'api_primary': 'https://api.brasil.io/microdados/v2/caged',
                'api_secondary': 'https://api.brasil.io/microdados/v2'
            },
            'INEP': {
                'api_primary': 'https://api.inep.gov.br/microdados/v1/ideb',
                'api_secondary': 'https://api.inep.gov.br/microdados/v1'
            }
        }
        
        # Configuração de timeout e retry
        self.request_timeout = 30
        self.max_retries = 3
        retry_delays = [1, 2, 4]  # segundos
        
        # Métricas
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls': 0,
            'fallback_activated': 0,
            'source_success': {source: 0 for source in self.fallback_sources}
        }
    
    def _get_cache_key(self, source: str, indicator: str, params: Dict = None) -> str:
        """Gera chave única para cache."""
        params_str = json.dumps(params or {}, sort_keys=True)
        return f"{source}_{indicator}_{hash(params_str)}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Recupera dados do cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Verificar se o cache ainda é válido
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            source_type = cache_data['source_type']
            
            if datetime.now() - cached_at > self.cache_ttl[source_type]:
                cache_file.unlink()  # Remove cache expirado
                self.metrics['cache_misses'] += 1
                return None
            
            self.metrics['cache_hits'] += 1
            return pd.DataFrame(cache_data['data'])
            
        except Exception as e:
            logger.error(f"Erro ao ler cache {cache_key}: {e}")
            self.metrics['cache_misses'] += 1
            return None
    
    def _save_to_cache(self, cache_key: str, data: pd.DataFrame, source_type: str):
        """Salva dados no cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            cache_data = {
                'cached_at': datetime.now().isoformat(),
                'source_type': source_type,
                'data': data.to_dict('records')
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Dados cacheados para {cache_key} (fonte: {source_type})")
            
        except Exception as e:
            logger.error(f"Erro ao salvar cache {cache_key}: {e}")
    
    async def _fetch_from_api(self, source: str, indicator: str, params: Dict = None) -> Optional[pd.DataFrame]:
        """Busca dados de API primária."""
        try:
            endpoints = self.api_endpoints.get(source, {})
            url = endpoints.get('api_primary')
            
            if not url:
                return None
            
            # Adicionar parâmetros à URL
            if params:
                query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                url += f"?{query_string}"
            
            headers = {
                'User-Agent': 'Painel-GV/1.0',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=self.request_timeout)
            response.raise_for_status()
            
            self.metrics['api_calls'] += 1
            self.metrics['source_success'][source] += 1
            
            # Processar resposta JSON
            data = response.json()
            
            # Converter para DataFrame (implementação específica por API)
            df = self._process_api_response(source, data, indicator)
            
            if df is not None and not df.empty:
                logger.info(f"Dados obtidos da API primária {source}/{indicator}")
                return df
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Erro na API primária {source}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado na API {source}: {e}")
            return None
    
    def _fetch_from_csv(self, source: str, indicator: str, params: Dict = None) -> Optional[pd.DataFrame]:
        """Busca dados de arquivo CSV fallback."""
        try:
            # Buscar arquivos CSV na pasta data/raw
            raw_dir = DATA_DIR / "raw"
            csv_files = list(raw_dir.glob(f"*{source.lower()}*.csv"))
            
            if not csv_files:
                return None
            
            # Usar o arquivo mais recente
            latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
            
            # Tentar diferentes encodings e delimitadores
            for encoding in ['utf-8', 'latin-1']:
                for delimiter in [';', ',', '\t']:
                    try:
                        df = pd.read_csv(latest_file, encoding=encoding, delimiter=delimiter)
                        if not df.empty:
                            logger.info(f"Dados lidos do CSV {source}: {latest_file.name}")
                            return df
                    except:
                        continue
            
            logger.warning(f"Não foi possível ler arquivo CSV para {source}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao ler CSV {source}: {e}")
            return None
    
    def _fetch_from_converted_xlsx(self, source: str, indicator: str, params: Dict = None) -> Optional[pd.DataFrame]:
        """Busca dados de arquivo XLSX convertido."""
        try:
            converted_dir = DATA_DIR / "raw" / "converted"
            xlsx_files = list(converted_dir.glob(f"*{source.lower()}*.xlsx"))
            
            if not xlsx_files:
                return None
            
            # Usar o arquivo mais recente
            latest_file = max(xlsx_files, key=lambda f: f.stat().st_mtime)
            
            df = pd.read_excel(latest_file)
            
            if not df.empty:
                logger.info(f"Dados lidos do XLSX convertido {source}: {latest_file.name}")
                return df
                
        except Exception as e:
            logger.error(f"Erro ao ler XLSX {source}: {e}")
            return None
    
    def _process_api_response(self, source: str, data: Dict, indicator: str) -> Optional[pd.DataFrame]:
        """Processa resposta específica de cada API."""
        if source == 'IBGE':
            return self._process_ibge_response(data, indicator)
        elif source == 'CAGED':
            return self._process_caged_response(data, indicator)
        elif source == 'INEP':
            return self._process_ideb_response(data, indicator)
        else:
            # Processamento genérico
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                return pd.DataFrame([data])
            return None
    
    def _process_ibge_response(self, data: Dict, indicator: str) -> Optional[pd.DataFrame]:
        """Processa resposta da API do IBGE."""
        try:
            # Implementação específica para IBGE
            if 'resultados' in data:
                df = pd.DataFrame(data['resultados'])
                return df
            elif isinstance(data, list):
                return pd.DataFrame(data)
            return None
        except Exception as e:
            logger.error(f"Erro ao processar resposta IBGE: {e}")
            return None
    
    def _process_caged_response(self, data: Dict, indicator: str) -> Optional[pd.DataFrame]:
        """Processa resposta da API do CAGED."""
        try:
            # Implementação específica para CAGED
            if 'resultados' in data:
                df = pd.DataFrame(data['resultados'])
                return df
            elif isinstance(data, list):
                return pd.DataFrame(data)
            return None
        except Exception as e:
            logger.error(f"Erro ao processar resposta CAGED: {e}")
            return None
    
    def _process_ideb_response(self, data: Dict, indicator: str) -> Optional[pd.DataFrame]:
        """Processa resposta da API do INEP."""
        try:
            # Implementação específica para IDEB
            if 'resultados' in data:
                df = pd.DataFrame(data['resultados'])
                return df
            elif isinstance(data, list):
                return pd.DataFrame(data)
            return None
        except Exception as e:
            logger.error(f"Erro ao processar resposta INEP: {e}")
            return None
    
    async def get_data_with_fallback(self, source: str, indicator: str, params: Dict = None) -> Optional[pd.DataFrame]:
        """
        Busca dados com sistema de fallback robusto.
        
        Args:
            source: Fonte de dados (IBGE, CAGED, etc.)
            indicator: Indicador específico
            params: Parâmetros adicionais
            
        Returns:
            DataFrame com dados ou None se todas as fontes falharem
        """
        cache_key = self._get_cache_key(source, indicator, params)
        
        # Verificar cache primeiro
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Tentar fontes em ordem de prioridade
        for source_type in self.fallback_sources.get(source, []):
            try:
                if source_type == 'api_primary':
                    data = await self._fetch_from_api(source, indicator, params)
                elif source_type == 'api_secondary':
                    data = await self._fetch_from_api(source, indicator, params)
                elif source_type == 'csv_fallback':
                    data = self._fetch_from_csv(source, indicator, params)
                elif source_type == 'converted_xlsx':
                    data = self._fetch_from_converted_xlsx(source, indicator, params)
                
                if data is not None and not data.empty:
                    self._save_to_cache(cache_key, data, source_type)
                    self.metrics['source_success'][source_type] += 1
                    return data
                    
            except Exception as e:
                logger.warning(f"Fallback {source_type} failed for {source}/{indicator}: {e}")
                self.metrics['fallback_activated'] += 1
                continue
        
        logger.error(f"Todas as fontes de fallback falharam para {source}/{indicator}")
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do sistema de fallback."""
        return {
            'cache_hit_rate': (
                self.metrics['cache_hits'] / 
                max(1, self.metrics['cache_hits'] + self.metrics['cache_misses'])
            ) * 100,
            'api_calls': self.metrics['api_calls'],
            'fallback_activated': self.metrics['fallback_activated'],
            'source_success': self.metrics['source_success'],
            'cache_hits': self.metrics['cache_hits'],
            'cache_misses': self.metrics['cache_misses']
        }
    
    def clear_cache(self, source: str = None):
        """Limpa cache."""
        if source:
            # Limpar cache específico
            pattern = f"{source}_*"
            for cache_file in self.cache_dir.glob(pattern):
                cache_file.unlink()
        else:
            # Limpar todo o cache
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        
        # Resetar métricas
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls': 0,
            'fallback_activated': 0,
            'source_success': {source: 0 for source in self.fallback_sources}
        }
        
        logger.info("Cache limpo")
    
    def get_cache_info(self) -> List[Dict[str, Any]]:
        """Retorna informações sobre o cache."""
        cache_info = []
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                cache_info.append({
                    'file': cache_file.name,
                    'indicator': cache_file.name.split('_')[1] if '_' in cache_file.name else cache_file.name.replace('.json', ''),
                    'source': cache_data.get('source_type', 'unknown'),
                    'cached_at': cache_data['cached_at'],
                    'size_bytes': cache_file.stat().st_size,
                    'expired': datetime.fromisoformat(cache_data['cached_at']) < datetime.now() - self.cache_ttl[cache_data.get('source_type', 'api_primary')]
                })
            except Exception as e:
                logger.error(f"Erro ao ler info do cache {cache_file}: {e}")
        
        return sorted(cache_info, key=lambda x: x['cached_at'], reverse=True)

# Instância global do gerenciador de fallback
fallback_manager = FallbackManager()
