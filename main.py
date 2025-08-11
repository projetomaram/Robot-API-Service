from fastapi import FastAPI, HTTPException
from os import getenv
import uvicorn
import requests

app = FastAPI()

OSRM_IP = getenv('OSRM_IP')
OVERPASS_IP = getenv('OP_IP')

# Coordinates format: (latitude, longitude)
@app.get("/robot-path/{coordinates}")
async def robot_path(coordinates : str):
    try:
        # Ponto inicial e ponto final definidos de forma crua 
        initial_point = coordinates.split(';')[0]
        final_point = coordinates.split(';')[1]
        
        # Formatando os pontos        
        initial_point = {"lat":initial_point.split(',')[0], "long":initial_point.split(',')[1]}
        final_point = {"lat":final_point.split(',')[0], "long": final_point.split(',')[1]}
        
        # OSRM request 
        response = requests.get(f"http://{OSRM_IP}:5000/route/v1/driving/{initial_point['long']},{initial_point['lat']};{final_point['long']},{final_point['lat']}?overview=false&annotations=nodes")
        # Filtering request (get only nodes)
        
        if response.status_code == 200:
            nodes = response.json()['routes'][0]['legs'][0]['annotation']['nodes']

        #Overpass request
        nodes_str = [f"node({node});\n" for node in nodes]
        request_payload = '''[out:json][timeout:25];
(\n'''
        for node_str in nodes_str:
            request_payload += node_str
        
        request_payload += '''  );
(._;>;);
out;'''
        
        response = requests.post(f"http://{OVERPASS_IP}:6060/api/interpreter", data=request_payload)
        
        if response.status_code == 200:
            overpass_data_filtered = response.json()['elements']
            return overpass_data_filtered
        return HTTPException(status_code=500, detail=f"Erro interno de requisicao: {response.json()}")  
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)