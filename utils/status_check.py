import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

from config import DATA_DIR, COD_IBGE, MUNICIPIO
from database import get_session, Indicator
from config.indicators import CATALOGO_INDICADORES, SOURCES_METADATA

logger = logging.getLogger(__name__)

# Cache simples em memória para status por indicador
_status_cache = {}
_cache_timestamp = {}
CACHE_DURATION = timedelta(minutes=30)  # Cache por 30 minutos

def _check_url_availability(url: str, timeout: int = 10) -> Tuple[bool, Optional[str]]:
    """Verifica se a URL responde com sucesso. Retorna (sucesso, erro_msg)."""
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return True, None
        else:
            return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)

def _get_latest_file_mtime(pattern: str) -> Optional[datetime]:
    """Retorna a data de modificação mais recente (datetime) para arquivos que correspondem ao padrão."""
    raw_dir = DATA_DIR / "raw"
    candidates = list(raw_dir.glob(pattern))
    if not candidates:
        return None
    latest_ts = max(f.stat().st_mtime for f in candidates)
    return datetime.fromtimestamp(latest_ts)

def _get_indicator_last_update(indicator_key: str, source: str) -> Optional[datetime]:
    """Retorna a data de coleta mais recente de um indicador no banco."""
    with get_session() as session:
        rec = session.query(Indicator).filter_by(
            indicator_key=indicator_key,
            source=source,
            municipality_code=str(COD_IBGE)
        ).order_by(Indicator.collected_at.desc()).first()
        return rec.collected_at if rec else None

def get_indicator_status(indicator_key: str, source: str) -> Dict[str, str]:
    """
    Retorna o status de um indicador: {'status': 'ok'|'error'|'update', 'message': str, 'url': str}
    Usa cache para evitar múltiplas chamadas na mesma sessão.
    """
    cache_key = f"{indicator_key}_{source}"
    now = datetime.now()
    
    # Verificar cache
    if cache_key in _status_cache and cache_key in _cache_timestamp:
        if now - _cache_timestamp[cache_key] < CACHE_DURATION:
            return _status_cache[cache_key]
    
    meta = CATALOGO_INDICADORES.get(indicator_key, {})
    src_meta = SOURCES_METADATA.get(source, {})
    url = src_meta.get("url", "")
    auto = src_meta.get("auto_update", False)
    manual = src_meta.get("manual_check", False)

    result = {"status": "ok", "message": "", "url": url}

    # Fonte automática: checar URL
    if auto:
        ok, err = _check_url_availability(url)
        if ok:
            result = {"status": "ok", "message": "", "url": url}
        else:
            result = {"status": "error", "message": f"Erro: Impossível atualizar — {err}", "url": url}

    # Fonte manual: comparar data do arquivo com data no banco
    elif manual:
        # Padrões específicos por fonte para melhor detecção
        patterns = _get_file_patterns(source, indicator_key)
        latest_mtime: Optional[datetime] = None
        for pat in patterns:
            mtime = _get_latest_file_mtime(pat)
            if mtime and (latest_mtime is None or mtime > latest_mtime):
                latest_mtime = mtime
        last_db = _get_indicator_last_update(indicator_key, source)

        if latest_mtime and last_db:
            if latest_mtime > last_db + timedelta(hours=24):
                result = {"status": "update", "message": "Atualizar", "url": url}
        result = {"status": "ok", "message": "", "url": url}

    # Salvar no cache
    _status_cache[cache_key] = result
    _cache_timestamp[cache_key] = now
    
    return result


def _get_file_patterns(source: str, indicator_key: str) -> list:
    """Retorna padrões de arquivo específicos por fonte para melhor detecção."""
    patterns = []
    
    # Padrões específicos por fonte
    source_patterns = {
        "SEEG": ["*seeg*.csv", "*SEEG*.csv"],
        "SEBRAE": ["*sebrae*.csv", "*Sebrae*.csv", "*SEBRAE*.csv"],
        "MapBiomas": ["*mapbiomas*.xlsx", "*MapBiomas*.xlsx", "*MAPBIOMAS*.xlsx"],
        "INEP": ["*sinopse*.xlsx", "*Sinopse*.xlsx", "*SINOPSE*.xlsx"],
        "DataSUS": ["*datasus*.csv", "*DataSUS*.csv", "*obitos*.csv"],
        "SEFAZ-MG": ["*vaf*.csv", "*VAF*.csv", "*icms*.csv"],
        "IDSC-BR": ["*idsc*.xlsx", "*IDSC*.xlsx"],
        "RAIS": ["*rais*.xlsx", "*RAIS*.xlsx"],
        "CAGED": ["*caged*.xlsx", "*CAGED*.xlsx"],
        "SNIS": ["*snis*.csv", "*SNIS*.csv"]
    }
    
    # Adicionar padrões da fonte
    if source in source_patterns:
        patterns.extend(source_patterns[source])
    
    # Adicionar padrões genéricos do indicador
    patterns.extend([f"*{source.lower()}*", f"*{indicator_key.lower()}*"])
    
    return patterns

def get_all_indicators_status() -> Dict[str, Dict[str, str]]:
    """Retorna status para todos os indicadores conhecidos."""
    status_map = {}
    for key, meta in CATALOGO_INDICADORES.items():
        source = meta.get("fonte", "")
        status_map[key] = get_indicator_status(key, source)
    return status_map
