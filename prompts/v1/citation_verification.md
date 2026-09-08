# Prompt version: v1

# Citation verification prompt

You are a citation verifier.

For each claim-citation pair, decide whether the cited chunk actually supports the claim.

Return JSON: {{"results": [{{"claim": "...", "chunk_id": "...", "supported": true|false}}]}}

CLAIMS:
{claims}

CHUNKS:
{chunks}
