# Guia de Integração - API de Pagamentos PIX

Este documento descreve como integrar a aplicação de pagamentos PIX (Django + Mercado Pago) com outras aplicações.

## Sumário
1. [Visão Geral](#visão-geral)
2. [Endpoints da API](#endpoints-da-api)
   - [Gerar Pagamento](#gerar-pagamento)
   - [Verificar Status](#verificar-status)
   - [Webhook](#webhook)
3. [Exemplos de Integração](#exemplos-de-integração)
   - [JavaScript (Fetch)](#javascript-fetch)
   - [Python (Requests)](#python-requests)
4. [Configuração de Ambiente](#configuração-de-ambiente)

---

## Visão Geral

A aplicação funciona como um serviço de backend que gerencia a comunicação com o Mercado Pago para criar cobranças PIX e monitorar seus status. Ela expõe endpoints REST que aceitam e retornam JSON.

## Endpoints da API

### Gerar Pagamento

Cria uma nova transação PIX e retorna o código "Copia e Cola" e o QR Code em Base64.

- **URL:** `/generate-payment/`
- **Método:** `POST`
- **Corpo da Requisição (JSON):**

| Campo | Tipo | Obrigatório | Descrição |
| :--- | :--- | :--- | :--- |
| `price` | float | Sim | Valor do pagamento. |
| `description` | string | Sim | Descrição da cobrança. |
| `payer` | object | Não | Dados do pagador (opcional, usa padrões do `.env` se omitido). |

**Exemplo de corpo com pagador:**
```json
{
  "price": 50.0,
  "description": "Compra de Teste",
  "payer": {
    "email": "cliente@email.com",
    "first_name": "João",
    "last_name": "Silva",
    "identification": {
      "type": "CPF",
      "number": "12345678901"
    }
  }
}
```

**Resposta de Sucesso (200 OK):**
```json
{
  "transaction_id": 123456789,
  "clipboard": "000201010212430505...",
  "qrcode": "data:image/jpeg;base64,/9j/4AAQSkZJR..."
}
```

---

### Verificar Status

Consulta o status atual de uma transação específica.

- **URL:** `/verify-payment/`
- **Método:** `POST`
- **Corpo da Requisição (JSON):**

```json
{
  "transaction_id": 123456789
}
```

**Resposta de Sucesso (200 OK):**
```json
{
  "id": 123456789,
  "status": "approved",
  "status_detail": "accredited"
}
```

*Status comuns: `pending`, `approved`, `cancelled`, `rejected`.*

---

### Webhook

Endpoint para receber notificações automáticas do Mercado Pago quando o status de um pagamento muda.

- **URL:** `/webhook/`
- **Método:** `POST`
- **Configuração:** Você deve configurar esta URL no painel do Mercado Pago (ex: `https://seu-dominio.com/webhook/`).

---

## Exemplos de Integração

### JavaScript (Fetch)

```javascript
// Gerar um pagamento
async function createPix(amount, desc) {
    const response = await fetch('https://seu-api.com/generate-payment/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            price: amount,
            description: desc
        })
    });
    const data = await response.json();
    console.log('ID:', data.transaction_id);
    console.log('Código Copia e Cola:', data.clipboard);
}

// Verificar status
async function checkStatus(id) {
    const response = await fetch('https://seu-api.com/verify-payment/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transaction_id: id })
    });
    const data = await response.json();
    if (data.status === 'approved') {
        alert('Pagamento aprovado!');
    }
}
```

### Python (Requests)

```python
import requests

api_url = "https://seu-api.com"

# Gerar pagamento
def gerar_pix(valor, descricao):
    payload = {
        "price": valor,
        "description": descricao
    }
    r = requests.post(f"{api_url}/generate-payment/", json=payload)
    return r.json()

# Verificar status
def verificar(id_transacao):
    payload = {"transaction_id": id_transacao}
    r = requests.post(f"{api_url}/verify-payment/", json=payload)
    return r.json()
```

## 4. Configuração de Segurança e CORS

Para que a aplicação `https://mypayments.store/` consiga fazer requisições para sua API de pagamentos, você **precisa** configurar o CORS (Cross-Origin Resource Sharing).

### Passo 1: Instalar dependência
```bash
pip install django-cors-headers
```

### Passo 2: Configurar `settings.py`
Adicione o seguinte ao seu arquivo de configurações:

```python
INSTALLED_APPS = [
    ...
    'corsheaders',
    ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', # Deve vir antes do CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    ...
]

# Permitir apenas o seu domínio de frontend
CORS_ALLOWED_ORIGINS = [
    "https://mypayments.store",
]
```

---

## 5. Exemplo Real de Integração (mypayments.store)

Abaixo, um exemplo de como você pode implementar o fluxo completo no seu frontend:

```javascript
const API_BASE_URL = 'https://sua-api-pix.com'; // URL onde este backend está rodando

// Função disparada ao clicar em "Pagar com PIX"
async function processarPagamento(valor) {
    try {
        const response = await fetch(`${API_BASE_URL}/generate-payment/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                price: valor,
                description: `Pagamento via mypayments.store - R$ ${valor}`,
                payer: {
                    email: "contato@mypayments.store"
                }
            })
        });

        const data = await response.json();

        if (data.transaction_id) {
            // 1. Mostrar QR Code para o usuário
            document.getElementById('qr-code-img').src = data.qrcode;

            // 2. Disponibilizar o "Copia e Cola"
            document.getElementById('pix-input').value = data.clipboard;

            // 3. Iniciar monitoramento do status
            iniciarMonitoramento(data.transaction_id);
        }
    } catch (error) {
        console.error("Erro ao gerar PIX:", error);
    }
```

---

## 6. Configuração de Ambiente (Backend)

Para que a API funcione corretamente, certifique-se de que as seguintes variáveis estão configuradas no arquivo `.env` da aplicação de pagamentos:

- `MERCADO_PAGO_ACCESS_TOKEN`: Seu token de acesso (Produção ou Teste).
- `ALLOWED_HOSTS`: Deve incluir o domínio onde este backend será hospedado.
- `DEFAULT_PAYER_*`: Dados que serão usados caso o frontend não envie o objeto `payer`.
- `DB_NAME`, `DB_USER`, etc: Configurações de conexão com seu banco de dados (MySQL recomendado).


