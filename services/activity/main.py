from fastapi import FastAPI
app = FastAPI(title='Activity Service')

@app.get('/')
async def root():
    return {'message': 'Hello World'}

@app.get('/lool')
async def lool():
    return {'message': 'Hello LOOOL'}