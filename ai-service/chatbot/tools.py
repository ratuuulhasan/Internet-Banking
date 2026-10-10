"""
Function calling tools — allows the chatbot to query the Django backend.
"""
import os
import requests

# Django backend URL — comes from .env
DJANGO_API = os.getenv('DJANGO_API_URL', 'http://localhost:8000/api')


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_account_balance",
            "description": "Get the user's current account balances. Use when user asks about balance or how much money they have.",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_type": {
                        "type": "string",
                        "enum": ["SAVINGS", "CURRENT", "ALL"],
                        "description": "Which account to check",
                    }
                },
                "required": ["account_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_transactions",
            "description": "Get user's recent transactions. Use when user asks about recent activity, last payments, or transaction history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "How many transactions to return (max 10)",
                        "default": 5,
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_kyc_status",
            "description": "Check user's KYC verification status. Use when user asks about KYC or account verification.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_loan_status",
            "description": "Get user's loan applications and their status.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def execute_tool(name: str, args: dict, auth_token: str) -> dict:
    """Call the Django backend tool endpoint."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    try:
        if name == "get_account_balance":
            r = requests.get(f"{DJANGO_API}/accounts/", headers=headers, timeout=5)
            accounts = r.json()
            if isinstance(accounts, dict):
                accounts = accounts.get('results', [])
            atype = args.get('account_type', 'ALL')
            if atype != 'ALL':
                accounts = [a for a in accounts if a.get('account_type') == atype]
            return {
                'accounts': [
                    {
                        'number': a['account_number'],
                        'type': a['account_type'],
                        'balance': a['balance'],
                        'currency': a.get('currency', 'BDT'),
                    }
                    for a in accounts
                ]
            }

        elif name == "get_recent_transactions":
            limit = min(int(args.get('limit', 5)), 10)
            r = requests.get(f"{DJANGO_API}/transactions/", headers=headers, timeout=5)
            txns = r.json()
            if isinstance(txns, dict):
                txns = txns.get('results', [])
            return {
                'transactions': [
                    {
                        'ref': t['reference_no'],
                        'type': t['transaction_type'],
                        'amount': t['amount'],
                        'status': t['status'],
                        'date': t['created_at'],
                    }
                    for t in txns[:limit]
                ]
            }

        elif name == "get_kyc_status":
            r = requests.get(f"{DJANGO_API}/kyc/", headers=headers, timeout=5)
            kycs = r.json()
            if isinstance(kycs, dict):
                kycs = kycs.get('results', [])
            if not kycs:
                return {'kyc': 'NOT_SUBMITTED'}
            return {
                'kyc': kycs[0].get('status', 'UNKNOWN'),
                'remarks': kycs[0].get('remarks', ''),
            }

        elif name == "get_loan_status":
            r = requests.get(f"{DJANGO_API}/loans/", headers=headers, timeout=5)
            loans = r.json()
            if isinstance(loans, dict):
                loans = loans.get('results', [])
            return {
                'loans': [
                    {
                        'type': l['loan_type'],
                        'amount': l['principal_amount'],
                        'status': l['status'],
                        'emi': l['monthly_emi'],
                    }
                    for l in loans
                ]
            }

    except Exception as e:
        return {'error': str(e)}

    return {'error': f'Unknown tool: {name}'}