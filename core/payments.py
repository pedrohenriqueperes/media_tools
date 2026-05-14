import requests
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)
PAYMENT_API_URL = os.getenv('PAYMENT_API_URL', 'https://mypayments.store')

def generate_pix_payment(price, description, user_email):
    """
    Chama a API externa para gerar um pagamento PIX.
    """
    url = f"{PAYMENT_API_URL}/generate-payment/"
    payload = {
        "price": float(price),
        "description": description,
        "payer": {
            "email": user_email
        }
    }

    try:
        logger.info(f"Gerando pagamento PIX: {url} | Payload: {payload}")
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Pagamento gerado com sucesso: {data.get('transaction_id')}")
        return data
    except requests.exceptions.RequestException as e:
        error_msg = f"Erro na API de pagamentos ({e})"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" - Resposta: {e.response.text}"
        logger.error(error_msg)
        print(f"DEBUG PAYMENT ERROR: {error_msg}")
        return None

def verify_pix_payment(transaction_id):
    """
    Verifica o status de um pagamento na API externa.
    """
    url = f"{PAYMENT_API_URL}/verify-payment/"
    payload = {
        "transaction_id": transaction_id
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao verificar pagamento: {e}")
        return None
