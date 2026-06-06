from fastapi import FastAPI
app = FastAPI(title='Bidding Service')

@app.get('/')
async def root():
    return {'message': 'Hello World'}

@app.get('/{auction_id}')
async def get_bid_at_auction(auction_id: str):
    return {'message': f'100 bids at auction {auction_id}'}