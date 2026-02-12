"""
Dashboard de Métricas do Sistema
Monitoramento em tempo real da saúde e performance do Painel GV.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Any

from monitoring.health_checker import health_checker
from utils.alert_manager import alert_manager
from utils.fallback_manager import fallback_manager
from config import MUNICIPIO, UF

def create_metrics_dashboard():
    """Cria dashboard de métricas do sistema."""
    st.title("📊 Dashboard de Métricas do Sistema")
    st.caption(f"**Monitoramento em Tempo Real** - {MUNICIPIO}/{UF}")
    
    # Atualização automática
    if st.button("🔄 Atualizar Métricas"):
        st.rerun()
    
    # Status Geral
    st.subheader("📈 Status Geral do Sistema")
    
    health_status = health_checker.check_all_components()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_emoji = "✅" if health_status['status'] == 'healthy' else "⚠️"
        st.metric("📈 Status Geral", f"{status_emoji} {health_status['status'].title()}")
    
    with col2:
        score = health_status['overall_score']
        st.metric("🎯 Score Saúde", f"{score:.2f}", f"{(score-0.95)*100:+.1f}%")
    
    with col3:
        issues_count = len(health_status['issues'])
        st.metric("⚠️ Issues", f"{issues_count}", f"{issues_count:+0}")
    
    with col4:
        alerts_count = len(alert_manager.alert_history)
        st.metric("📊 Alertas", f"{alerts_count}", f"{alerts_count:+0}")
    
    # Componentes Detalhados
    st.subheader("🔍 Detalhes dos Componentes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔄 APIs Externas")
        
        api_health = health_status['components']['apis']
        
        # Criar gráfico de status das APIs
        api_data = []
        for source, status in api_health['sources'].items():
            api_data.append({
                'API': source,
                'Status': status['status'],
                'Response Time (ms)': status.get('response_time', 0),
                'Error Count': status.get('error_count', 0)
            })
        
        if api_data:
            df_apis = pd.DataFrame(api_data)
            
            # Gráfico de barras de tempo de resposta
            fig = px.bar(df_apis, x='API', y='Response Time (ms)', 
                         title="Tempo de Resposta das APIs",
                         color='Status',
                         color_discrete_map={'healthy': 'green', 'degraded': 'orange', 'error': 'red'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela detalhada
            st.dataframe(df_apis, use_container_width=True)
    
    with col2:
        st.subheader("📊 Métricas de Cache")
        
        cache_metrics = fallback_manager.get_metrics()
        
        # Métricas do cache
        col_cache1, col_cache2, col_cache3 = st.columns(3)
        
        with col_cache1:
            st.metric("📈 Cache Hit Rate", f"{cache_metrics['cache_hit_rate']:.1f}%")
        
        with col_cache2:
            st.metric("📊 Cache Hits", f"{cache_metrics['cache_hits']}")
        
        with col_cache3:
            st.metric("🔄 API Calls", f"{cache_metrics['api_calls']}")
        
        # Gráfico de pizza de sucesso por fonte
        source_data = []
        for source, success in cache_metrics['source_success'].items():
            if success > 0:
                source_data.append({
                    'Fonte': source,
                    'Sucessos': success
                })
        
        if source_data:
            df_sources = pd.DataFrame(source_data)
            
            fig = px.pie(df_sources, values='Sucessos', names='Fonte', 
                         title="Sucessos por Fonte de Dados")
            st.plotly_chart(fig, use_container_width=True)
    
    # ETL Status
    st.subheader("🔄 Status dos Processos ETL")
    
    etl_health = health_status['components']['etl']
    
    col_etl1, col_etl2, col_etl3 = st.columns(3)
    
    with col_etl1:
        etl_status_emoji = "✅" if etl_health['status'] == 'healthy' else "⚠️"
        st.metric("🔄 ETL Status", f"{etl_status_emoji} {etl_health['status'].title()}")
    
    with col_etl2:
        failure_rate = etl_health['failure_rate']
        st.metric("⚠️ Taxa de Falha", f"{failure_rate:.2%}")
    
    with col_etl3:
        if etl_health['last_run']:
            last_run = datetime.fromisoformat(etl_health['last_run'])
            hours_ago = (datetime.now() - last_run).total_seconds() / 3600
            st.metric("📅 Última Execução", f"{hours_ago:.1f}h atrás")
    
    # Database Status
    st.subheader("🗄️ Status do Banco de Dados")
    
    db_health = health_status['components']['database']
    
    col_db1, col_db2, col_db3 = st.columns(3)
    
    with col_db1:
        db_status_emoji = "✅" if db_health['status'] == 'healthy' else "⚠️"
        st.metric("🗄️ DB Status", f"{db_status_emoji} {db_health['status'].title()}")
    
    with col_db2:
        st.metric("📊 Tabelas", f"{db_health['table_count']}")
    
    with col_db3:
        if db_health['connection_time']:
            st.metric("⚡ Conexão", f"{db_health['connection_time']:.0f}ms")
    
    # Alertas Recentes
    st.subheader("📊 Alertas Recentes")
    
    recent_alerts = alert_manager.alert_history[-10:]
    
    if recent_alerts:
        # Converter para DataFrame
        alert_data = []
        for alert in recent_alerts:
            alert_data.append({
                'Timestamp': alert['timestamp'],
                'Tipo': alert['type'],
                'Prioridade': alert['priority'],
                'Mensagem': alert['message']
            })
        
        df_alerts = pd.DataFrame(alert_data)
        
        # Formatar timestamp
        df_alerts['Timestamp'] = pd.to_datetime(df_alerts['Timestamp'])
        df_alerts['Timestamp'] = df_alerts['Timestamp'].dt.strftime('%d/%m %H:%M')
        
        st.dataframe(df_alerts, use_container_width=True)
        
        # Gráfico de alertas por tipo
        alert_counts = df_alerts['Tipo'].value_counts()
        
        fig = px.bar(x=alert_counts.index, y=alert_counts.values,
                     title="Alertas por Tipo",
                     labels={'x': 'Tipo', 'y': 'Quantidade'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma alerta registrada recentemente.")
    
    # Timeline de Eventos
    st.subheader("📈 Timeline de Eventos")
    
    # Combinar eventos de diferentes fontes
    events = []
    
    # Adicionar eventos de alertas
    for alert in alert_manager.alert_history[-5:]:
        events.append({
            'timestamp': datetime.fromisoformat(alert['timestamp']),
            'type': 'alert',
            'message': f"[{alert['type'].upper()}] {alert['message']}"
        })
    
    # Adicionar eventos de health check
    events.append({
        'timestamp': datetime.fromisoformat(health_status['timestamp']),
        'type': 'health_check',
        'message': f"Health check: {health_status['status']}"
    })
    
    # Ordenar por timestamp
    events.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Exibir timeline
    for event in events:
        timestamp_str = event['timestamp'].strftime('%d/%m %H:%M')
        
        if event['type'] == 'alert':
            st.warning(f"📊 {timestamp_str}: {event['message']}")
        elif event['type'] == 'health_check':
            st.info(f"🔍 {timestamp_str}: {event['message']}")
    
    # Métricas de Performance
    st.subheader("⚡ Métricas de Performance")
    
    col_perf1, col_perf2, col_perf3, col_perf4 = st.columns(4)
    
    with col_perf1:
        st.metric("📈 Cache Hit Rate", f"{cache_metrics['cache_hit_rate']:.1f}%")
    
    with col_perf2:
        st.metric("🔄 API Calls", f"{cache_metrics['api_calls']}")
    
    with col_perf3:
        st.metric("⚠️ Fallbacks", f"{cache_metrics['fallback_activated']}")
    
    with col_perf4:
        total_requests = cache_metrics['cache_hits'] + cache_metrics['cache_misses']
        st.metric("📊 Total Requests", f"{total_requests}")
    
    # Gráfico de performance ao longo do tempo
    st.subheader("📈 Performance ao Longo do Tempo")
    
    # Placeholder para gráfico temporal
    st.info("Gráfico temporal de performance em desenvolvimento.")
    
    # Ações de Manutenção
    st.subheader("🔧 Ações de Manutenção")
    
    col_action1, col_action2, col_action3 = st.columns(3)
    
    with col_action1:
        if st.button("🗑️ Limpar Cache", type="secondary"):
            fallback_manager.clear_cache()
            st.success("Cache limpo com sucesso!")
    
    with col_action2:
        if st.button("🔄 Forçar Health Check", type="secondary"):
            health_status = health_checker.run_health_check()
            st.success("Health check executado!")
    
    with col_action3:
        if st.button("📊 Exportar Métricas", type="secondary"):
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'health_status': health_status,
                'cache_metrics': cache_metrics,
                'alert_count': len(alert_manager.alert_history)
            }
            st.json(metrics_data)
    
    # Informações do Sistema
    st.subheader("ℹ️ Informações do Sistema")
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.markdown(f"""
        **Configuração:**
        - Município: {MUNICIPIO}/{UF}
        - Cache TTL: 1-7 dias (por fonte)
        - Health Check: A cada 5 minutos
        - Alert Cooldown: 30 minutos
        """)
    
    with col_info2:
        st.markdown(f"""
        **Métricas Atuais:**
        - Score Saúde: {health_status['overall_score']:.2f}
        - Cache Hit Rate: {cache_metrics['cache_hit_rate']:.1f}%
        - APIs Ativas: {len(api_health['sources'])}
        - Alertas Hoje: {len(alert_manager.alert_history)}
        """)

def get_system_summary() -> Dict[str, Any]:
    """Retorna resumo completo do sistema."""
    health_status = health_checker.check_all_components()
    cache_metrics = fallback_manager.get_metrics()
    
    return {
        'timestamp': datetime.now().isoformat(),
        'health_status': health_status['status'],
        'health_score': health_status['overall_score'],
        'cache_hit_rate': cache_metrics['cache_hit_rate'],
        'active_alerts': len(alert_manager.alert_history),
        'apis_healthy': len([s for s in health_status['components']['apis']['sources'] 
                             if s['status'] == 'healthy']),
        'total_apis': len(health_status['components']['apis']['sources']),
        'last_health_check': health_status['timestamp']
    }
