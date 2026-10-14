"""Accept equivalent independent-review fields while preserving source records."""
def normalized(review):
    return {**review,'completion_basis':review.get('completion_basis') or review.get('basis') or '',
            'evidence_files':review.get('evidence_files') or review.get('evidence') or [],
            'review_limitations':review.get('review_limitations') or review.get('limitations') or []}
