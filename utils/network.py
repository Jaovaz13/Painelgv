import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def safe_request(url: str, method: str = "GET", timeout: int = 30, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Realiza uma requisição HTTP segura com tratamento de erros padrão.
    
    Args:
        url: URL alvo.
        method: Verbo HTTP (GET, POST, etc).
        timeout: Tempo limite em segundos.
        **kwargs: Argumentos extras para requests (headers, verify, etc).
        
    Returns:
        JSON da resposta se sucesso (200-299), ou None se erro.
    """
    try:
        if method.upper() == "GET":
            resp = requests.get(url, timeout=timeout, **kwargs)
        elif method.upper() == "POST":
            resp = requests.post(url, timeout=timeout, **kwargs)
        else:
            resp = requests.request(method, url, timeout=timeout, **kwargs)
            
        resp.raise_for_status()
        
        # Algumas APIs retornam 200 mas com success=False no corpo (ex: CKAN as vezes)
        # Tratamento básico de JSON
        return resp.json()
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"Erro HTTP ao acessar {url}: {e}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Erro de Conexão ao acessar {url}: {e}")
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout ao acessar {url}: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição para {url}: {e}")
    except ValueError:
        logger.error(f"Erro ao decodificar JSON de {url}")
        
    return None
