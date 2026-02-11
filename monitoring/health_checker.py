"""
Sistema de Health Checks para Monitoramento do Sistema
Implementa verificação contínua da saúde de APIs, dados e processos.
"""

import logging
import asyncio
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from config import DATA_DIR, COD_IBGE, MUNICIPIO, UF
from utils.fallback_manager import fallback_manager
from utils.alert_manager import alert_manager

logger = logging.getLogger(__name__)

class HealthChecker:
    """Verificador de saúde do sistema Painel GV."""
    
    def __init__(self):
        self.fallback_manager = fallback_manager
        self.alert_manager = alert_manager
        
        # Configurações de timeout
        self.api_timeout = 10
        self.db_timeout = 5
        
        # Status cache para evitar verificações excessivas
        self.status_cache = {}
        self.cache_duration = timedelta(minutes=5)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica se o cache ainda é válido."""
        if cache_key not in self.status_cache:
            return False
        
        cached_at = self.status_cache[cache_key]['timestamp']
        return datetime.now() - cached_at < self.cache_duration
    
    def _save_to_cache(self, cache_key: str, status: Dict[str, Any]):
        """Salva status no cache."""
        self.status_cache[cache_key] = {
            'timestamp': datetime.now(),
            'status': status
        }
    
    def check_api_health(self, api_name: str = None) -> Dict[str, Any]:
        """Verifica saúde de APIs específicas ou de todas."""
        cache_key = f"api_health_{api_name or 'all'}"
        
        # Verificar cache
        if self._is_cache_valid(cache_key):
            return self.status_cache[cache_key]['status']
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'sources': {},
            'issues': []
        }
        
        if api_name:
            # Verificar API específica
            status = self._check_single_api(api_name)
            health_status['sources'][api_name] = status
            if status['status'] != 'healthy':
                health_status['status'] = 'degraded'
                health_status['issues'].append(f"{api_name}: {status['message']}")
        else:
            # Verificar todas as APIs configuradas
            for source in self.fallback_manager.fallback_sources.keys():
                status = self._check_single_api(source)
                health_status['sources'][source] = status
                if status['status'] != 'healthy':
                    health_status['status'] = 'degraded'
                    health_status['issues'].append(f"{source}: {status['message']}")
        
        # Salvar no cache
        self._save_to_cache(cache_key, health_status)
        return health_status
    
    def _check_single_api(self, api_name: str) -> Dict[str, Any]:
        """Verifica saúde de uma API específica."""
        status = {
            'status': 'healthy',
            'message': '',
            'response_time': None,
            'last_check': None,
            'error_count': 0
        }
        
        try:
            endpoints = self.fallback_manager.api_endpoints.get(api_name, {})
            url = endpoints.get('api_primary')
            
            if not url:
                status['status'] = 'not_configured'
                status['message'] = f"API {api_name} não configurada"
                return status
            
            # Medir tempo de resposta
            start_time = time.time()
            response = requests.head(url, timeout=self.api_timeout)
            response_time = time.time() - start_time
            
            status['response_time'] = response_time * 1000  # Converter para ms
            status['last_check'] = datetime.now().isoformat()
            
            if response.status_code == 200:
                status['status'] = 'healthy'
            elif response.status_code >= 500:
                status['status'] = 'error'
                status['message'] = f"HTTP {response.status_code}"
            elif response.status_code >= 400:
                status['status'] = 'degraded'
                status['message'] = f"HTTP {response.status_code}"
            
        except requests.exceptions.Timeout:
            status['status'] = 'timeout'
            status['message'] = "Timeout"
            status['error_count'] += 1
        except requests.exceptions.RequestException as e:
            status['status'] = 'error'
            status['message'] = str(e)
            status['error_count'] += 1
        except Exception as e:
            status['status'] = 'error'
            status['message'] = f"Erro inesperado: {str(e)}"
            status['error_count'] += 1
        
        return status
    
    def check_database_health(self) -> Dict[str, Any]:
        """Verifica saúde do banco de dados."""
        cache_key = "database_health"
        
        if self._is_cache_valid(cache_key):
            return self.status_cache[cache_key]['status']
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'message': '',
            'connection_time': None,
            'last_query': None,
            'table_count': 0,
            'error_count': 0
        }
        
        try:
            from database import get_session
            
            # Testar conexão
            start_time = time.time()
            with get_session() as session:
                # Contar tabelas
                from sqlalchemy import text
                result = session.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")).fetchone()
                status['table_count'] = result[0] if result else 0
                
                # Testar query simples
                result = session.execute(text("SELECT COUNT(*) FROM indicators LIMIT 1")).fetchone()
                status['last_query'] = datetime.now().isoformat()
                
            status['connection_time'] = (time.time() - start_time) * 1000
            status['status'] = 'healthy'
            
        except Exception as e:
            status['status'] = 'error'
            status['message'] = str(e)
            status['error_count'] += 1
        
        self._save_to_cache(cache_key, status)
        return status
    
    def check_etl_health(self) -> Dict[str, Any]:
        """Verifica saúde dos processos ETL."""
        cache_key = "etl_health"
        
        if self._is_cache_valid(cache_key):
            return self.status_cache[cache_key]['status']
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'message': '',
            'last_run': None,
            'failure_rate': 0.0,
            'processed_indicators': 0
        }
        
        try:
            # Verificar logs do ETL
            etl_log = DATA_DIR / "logs" / "etl.log"
            if etl_log.exists():
                with open(etl_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-50:]  # Últimas 50 linhas
                    
                # Contar falhas recentes
                recent_errors = sum(1 for line in lines if 'ERROR' in line)
                recent_total = len(lines)
                
                if recent_total > 0:
                    status['failure_rate'] = recent_errors / recent_total
                    if status['failure_rate'] > 0.05:  # 5% de falha
                        status['status'] = 'degraded'
                        status['message'] = f"Taxa de falha no ETL: {status['failure_rate']:.2%}"
                
                # Buscar última execução bem-sucedida
                for line in reversed(lines):
                    if 'Job de atualização finalizado' in line:
                        import re
                        match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                        if match:
                            status['last_run'] = match.group(0)
                            break
                            
        except Exception as e:
            status['status'] = 'error'
            status['message'] = f"Erro ao verificar logs do ETL: {e}"
        
        self._save_to_cache(cache_key, status)
        return status
    
    def check_cache_health(self) -> Dict[str, Any]:
        """Verifica saúde do sistema de cache."""
        cache_key = "cache_health"
        
        if self._is_cache_valid(cache_key):
            return self.status_cache[cache_key]['status']
        
        metrics = self.fallback_manager.get_metrics()
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'message': '',
            'hit_rate': metrics['cache_hit_rate'],
            'total_requests': metrics['cache_hits'] + metrics['cache_misses'],
            'cache_size': len(list(self.fallback_manager.cache_dir.glob("*.json")))
        }
        
        if status['hit_rate'] < 0.7:  # 70% mínimo
            status['status'] = 'degraded'
            status['message'] = f"Taxa de cache baixa: {status['hit_rate']:.2f}%"
        
        self._save_to_cache(cache_key, status)
        return status
    
    def check_all_components(self) -> Dict[str, Any]:
        """Verifica saúde de todos os componentes do sistema."""
        cache_key = "all_components"
        
        if self._is_cache_valid(cache_key):
            return self.status_cache[cache_key]['status']
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'components': {},
            'issues': [],
            'overall_score': 1.0
        }
        
        # Verificar cada componente
        components = {
            'apis': self.check_api_health(),
            'database': self.check_database_health(),
            'etl': self.check_etl_health(),
            'cache': self.check_cache_health()
        }
        
        scores = []
        issues = []
        
        for component, status in components.items():
            health_status['components'][component] = status
            
            # Calcular pontuação do componente
            if status['status'] == 'healthy':
                score = 1.0
            elif status['status'] == 'degraded':
                score = 0.7
            else:  # error
                score = 0.3
            
            scores.append(score)
            
            # Compilar issues
            if status['issues']:
                issues.extend([f"{component}: {issue}" for issue in status['issues']])
        
        # Calcular pontuação geral
        if scores:
            health_status['overall_score'] = sum(scores) / len(scores)
        
        # Definir status geral
        if health_status['overall_score'] < 0.8:
            health_status['status'] = 'degraded'
        elif health_status['overall_score'] < 0.5:
            health_status['status'] = 'critical'
        
        health_status['issues'] = issues
        
        # Salvar no cache
        self._save_to_cache(cache_key, health_status)
        
        # Enviar alertas se necessário
        if health_status['status'] != 'healthy':
            self.alert_manager._send_alerts(issues)
        
        return health_status
    
    def get_health_summary(self) -> str:
        """Retorna resumo da saúde do sistema."""
        health_status = self.check_all_components()
        
        summary_lines = [
            f"Status Geral: {health_status['status'].upper()}",
            f"Score: {health_status['overall_score']:.2f}",
            f"Componentes verificados: {len(health_status['components'])}",
            f"Alertas ativas: {len(self.alert_manager.alert_history)}"
        ]
        
        if health_status['issues']:
            summary_lines.append("Problemas identificados:")
            for issue in health_status['issues'][:5]:
                summary_lines.append(f"• {issue}")
        
        return "\n".join(summary_lines)
    
    def create_health_dashboard(self) -> Dict[str, Any]:
        """Cria dados para dashboard de saúde."""
        health_status = self.check_all_components()
        
        dashboard_data = {
            'timestamp': health_status['timestamp'],
            'overall_status': health_status['status'],
            'overall_score': health_status['overall_score'],
            'components': health_status['components'],
            'metrics': {
                component: health_status['components']
            },
            'recent_alerts': self.alert_manager.alert_history[-10:]
        }
        
        return dashboard_data
    
    def run_continuous_monitoring(self, interval_minutes: int = 5):
        """Executa monitoramento contínuo."""
        logger.info("Iniciando monitoramento contínuo do sistema")
        
        while True:
            try:
                health_status = self.check_all_components()
                
                # Log do status
                if health_status['status'] != 'healthy':
                    logger.warning(f"Sistema em estado {health_status['status']}")
                
                # Enviar alertas se necessário
                if health_status['issues']:
                    logger.warning(f"Alertas ativas: {len(health_status['issues'])}")
                
                # Aguardar para próxima verificação
                time.sleep(interval_minutes * 60)  # Converter minutos para segundos
                
            except Exception as e:
                logger.error(f"Erro no monitoramento contínuo: {e}")
                time.sleep(interval_minutes * 60)
    
    def run_health_check(self) -> Dict[str, Any]:
        """Executa verificação única de saúde."""
        return self.check_all_components()

# Instância global do verificador de saúde
health_checker = HealthChecker()
