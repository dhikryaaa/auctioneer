from fastapi import FastAPI
app = FastAPI(title='Listing Service')

@app.get('/')
async def root():
    return {'message': 'Hello World'}

@app.get('/{id}')
async def get_auction(id: int):
    return {'message': f'getting auction with id {id}'}