"""
Sistema de Alertas Proativas para o Painel GV
Implementa monitoramento de saúde do sistema e envio de notificações.
"""

import logging
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from config import DATA_DIR, MUNICIPIO, UF, COD_IBGE

logger = logging.getLogger(__name__)

class AlertManager:
    """Gerenciador de alertas proativos para o sistema."""
    
    def __init__(self):
        self.thresholds = {
            'api_failure_rate': 0.1,  # 10% de falha de API
            'data_age_hours': 48,  # 48 horas sem atualização
            'etl_failure_rate': 0.05,  # 5% de falha no ETL
            'cache_hit_rate': 0.7,  # 70% de cache hit rate mínimo
            'system_error_rate': 0.02  # 2% de erro geral
        }
        
        self.alert_history = []
        self.alert_cooldown = timedelta(minutes=30)  # Evitar spam de alertas
        self.last_alerts = {}
        
        # Configuração de email (opcional)
        self.smtp_config = {
            'enabled': False,  # Desabilitado por padrão
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_user': '',
            'smtp_password': '',
            'from_email': f"alertas@{MUNICIPIO.lower().replace(' ', '')}.mg.gov.br",
            'to_emails': []
        }
        
        # Configuração do arquivo de log de alertas
        self.alerts_log = DATA_DIR / "logs" / "alerts.log"
        self.alerts_log.parent.mkdir(parents=True, exist_ok=True)
        
        # Configurar logging específico para alertas
        self.alert_logger = logging.getLogger('alerts')
        self.alert_logger.setLevel(logging.WARNING)
        
        # Criar handler para arquivo
        file_handler = logging.FileHandler(self.alerts_log, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
        ))
        self.alert_logger.addHandler(file_handler)
    
    def _send_email_alert(self, subject: str, message: str, priority: str = 'normal'):
        """Envia alerta por email."""
        if not self.smtp_config['enabled']:
            logger.info("Email alerts desabilitados")
            return
        
        try:
            msg = MIMEText(message)
            msg['Subject'] = f"[{priority.upper()}] {subject}"
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = self.smtp_config['to_emails']
            
            server = smtplib.SMTP(
                self.smtp_config['smtp_server'],
                self.smtp_config['smtp_port'],
                timeout=30
            )
            
            server.starttls()
            server.login(
                self.smtp_config['smtp_user'],
                self.smtp_config['smtp_password']
            )
            
            text = msg.as_string()
            server.sendmail(self.smtp_config['from_email'], 
                           self.smtp_config['to_emails'], text)
            
            logger.info(f"Email alert enviado: {subject}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
    
    def _send_slack_alert(self, message: str, priority: str = 'normal'):
        """Envia alerta para Slack (placeholder)."""
        # Implementar integração com Slack webhook
        logger.info(f"Slack alert: {message}")
        # TODO: Implementar integração real com Slack
    
    def _log_alert(self, alert_type: str, message: str, priority: str = 'normal', metadata: Dict = None):
        """Registra alerta no log."""
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'priority': priority,
            'message': message,
            'metadata': metadata or {}
        }
        
        self.alert_history.append(alert_data)
        self.alert_logger.warning(f"[{alert_type.upper()}] {message}")
        
        # Manter histórico de alertas (últimos 100)
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
    
    def _check_cooldown(self, alert_key: str) -> bool:
        """Verifica se ainda está em cooldown para evitar spam."""
        if alert_key not in self.last_alerts:
            return False
        
        last_alert_time = self.last_alerts[alert_key]
        return datetime.now() - last_alert_time < self.alert_cooldown
    
    def _set_cooldown(self, alert_key: str):
        """Define cooldown para um tipo de alerta."""
        self.last_alerts[alert_key] = datetime.now()
    
    def check_api_health(self) -> Dict[str, Any]:
        """Verifica saúde das APIs externas."""
        from utils.fallback_manager import fallback_manager
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'issues': [],
            'sources': {}
        }
        
        metrics = fallback_manager.get_metrics()
        
        for source in fallback_manager.fallback_sources.keys():
            source_metrics = {
                'status': 'healthy',
                'success_rate': 0.0,
                'last_check': None,
                'error_count': 0,
                'response_time': None
            }
            
            # Calcular taxa de sucesso
            total_calls = metrics['api_calls']
            successful_calls = metrics['source_success'].get(source, 0)
            
            if total_calls > 0:
                success_rate = successful_calls / total_calls
                source_metrics['success_rate'] = success_rate
                
                if success_rate < (1 - self.thresholds['api_failure_rate']):
                    source_metrics['status'] = 'degraded'
                    health_status['issues'].append(f"API {source}: Taxa de sucesso {success_rate:.2%}")
            
            health_status['sources'][source] = source_metrics
        
        # Verificar se há APIs degradadas
        degraded_sources = [source for source, status in health_status['sources'].items() if status['status'] == 'degraded']
        if degraded_sources:
            health_status['status'] = 'degraded'
        
        return health_status
    
    def check_data_freshness(self) -> Dict[str, Any]:
        """Verifica frescura dos dados no banco."""
        from database import get_session, Indicator
        from utils.fallback_manager import fallback_manager
        
        freshness_status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'fresh',
            'issues': [],
            'freshness_score': 1.0,
            'oldest_data': None,
            'stale_indicators': []
        }
        
        try:
            with get_session() as session:
                # Buscar dados mais antigos por fonte
                query = session.query(
                    Indicator.municipality_code == str(COD_IBGE),
                    Indicator.collected_at.desc()
                ).first()
                
                if query:
                    oldest_data = query.collected_at
                    freshness_status['oldest_data'] = oldest_data.isoformat()
                    
                    # Calcular idade em horas
                    age_hours = (datetime.now() - oldest_data).total_seconds() / 3600
                    
                    freshness_status['freshness_score'] = max(0, 1 - (age_hours / self.thresholds['data_age_hours']))
                    
                    if age_hours > self.thresholds['data_age_hours']:
                        freshness_status['status'] = 'stale'
                        freshness_status['issues'].append(f"Dados com {age_hours:.1f} horas sem atualização")
        
        except Exception as e:
            logger.error(f"Erro ao verificar frescura dos dados: {e}")
            freshness_status['status'] = 'error'
            freshness_status['issues'].append("Não foi possível verificar frescura dos dados")
        
        return freshness_status
    
    def check_etl_health(self) -> Dict[str, Any]:
        """Verifica saúde dos processos ETL."""
        etl_status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'issues': [],
            'last_run': None,
            'failure_rate': 0.0,
            'processed_indicators': 0
        }
        
        # Verificar logs do ETL
        etl_log = DATA_DIR / "logs" / "etl.log"
        if etl_log.exists():
            try:
                with open(etl_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-100:]  # Últimas 100 linhas
                    
                # Contar falhas recentes
                recent_errors = sum(1 for line in lines if 'ERROR' in line)
                recent_total = len(lines)
                
                if recent_total > 0:
                    etl_status['failure_rate'] = recent_errors / recent_total
                    if etl_status['failure_rate'] > self.thresholds['etl_failure_rate']:
                        etl_status['status'] = 'degraded'
                        etl_status['issues'].append(f"Taxa de falha no ETL: {etl_status['failure_rate']:.2%}")
                
                # Buscar última execução bem-sucedida
                for line in reversed(lines):
                    if 'Job de atualização finalizado' in line:
                        # Extrair timestamp
                        import re
                        match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                        if match:
                            etl_status['last_run'] = match.group(0)
                            break
                
            except Exception as e:
                logger.error(f"Erro ao verificar logs do ETL: {e}")
                etl_status['status'] = 'error'
                etl_status['issues'].append("Não foi possível verificar logs do ETL")
        
        return etl_status
    
    def check_cache_health(self) -> Dict[str, Any]:
        """Verifica saúde do sistema de cache."""
        from utils.fallback_manager import fallback_manager
        
        metrics = fallback_manager.get_metrics()
        
        cache_status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'issues': [],
            'hit_rate': metrics['cache_hit_rate'],
            'total_requests': metrics['cache_hits'] + metrics['cache_misses']
        }
        
        if cache_status['hit_rate'] < self.thresholds['cache_hit_rate']:
            cache_status['status'] = 'degraded'
            cache_status['issues'].append(f"Taxa de cache: {cache_status['hit_rate']:.2%}")
        
        return cache_status
    
    def check_system_health(self) -> Dict[str, Any]:
        """Verifica saúde geral do sistema."""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'issues': [],
            'metrics': {}
        }
        
        # Verificar cada componente
        api_status = self.check_api_health()
        data_status = self.check_data_freshness()
        etl_status = self.check_etl_health()
        cache_status = self.check_cache_health()
        
        health_status['metrics'] = {
            'apis': api_status,
            'data': data_status,
            'etl': etl_status,
            'cache': cache_status
        }
        
        # Compilar issues de todos os componentes
        all_issues = (
            api_status['issues'] + 
            data_status['issues'] + 
            etl_status['issues'] + 
            cache_status['issues']
        )
        
        if all_issues:
            health_status['status'] = 'degraded'
            health_status['issues'] = all_issues
            self._send_alerts(all_issues)
        
        return health_status
    
    def _send_alerts(self, issues: List[str]):
        """Envia alertas para os problemas identificados."""
        for issue in issues:
            alert_key = issue.split(':')[0] if ':' in issue else 'general'
            
            # Verificar cooldown
            if self._check_cooldown(alert_key):
                continue
            
            # Determinar prioridade
            if 'crítico' in issue.lower():
                priority = 'high'
            elif 'moderado' in issue.lower():
                priority = 'medium'
            else:
                priority = 'normal'
            
            # Enviar alerta
            self._log_alert('system', issue, priority)
            self._send_email_alert("Alerta do Sistema Painel GV", issue, priority)
            self._send_slack_alert(issue, priority)
            
            # Definir cooldown
            self._set_cooldown(alert_key)
    
    def create_alert_report(self) -> Dict[str, Any]:
        """Cria relatório completo de alertas."""
        recent_alerts = self.alert_history[-20:]
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_alerts': len(self.alert_history),
            'recent_alerts': recent_alerts,
            'metrics': self.get_system_metrics()
        }
        
        return report
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Retorna métricas gerais do sistema."""
        from utils.fallback_manager import fallback_manager
        
        return {
            'timestamp': datetime.now().isoformat(),
            'fallback_manager': fallback_manager.get_metrics(),
            'alert_history_count': len(self.alert_history),
            'last_alerts': self.last_alerts,
            'thresholds': self.thresholds
        }
    
    def get_alert_summary(self) -> str:
        """Retorna resumo das últimas alertas."""
        if not self.alert_history:
            return "Nenhuma alerta registrada recentemente."
        
        recent_alerts = self.alert_history[-5:]
        summary_lines = ["Resumo das últimas alertas:"]
        
        for alert in recent_alerts:
            timestamp = alert['timestamp']
            alert_type = alert['type']
            message = alert['message']
            summary_lines.append(f"• {timestamp}: [{alert_type.upper()}] {message}")
        
        return "\n".join(summary_lines)

# Instância global do gerenciador de alertas
alert_manager = AlertManager()
