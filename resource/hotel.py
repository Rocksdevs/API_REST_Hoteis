from models.site import SiteModel
from resource.site import Site
from flask_restful import Resource, reqparse
from models.hotel import HotelModel
from resource.filtros import normalize_path_params_,consulta_com__cidade,consulta_sem_cidade
from flask_jwt_extended import jwt_required
import sqlite3



path_params = reqparse.RequestParser()
path_params.add_argument('cidade', type=str)
path_params.add_argument('estrelas_min', type=float)
path_params.add_argument('estrelas_max', type=float)
path_params.add_argument('diaria_min', type=float)
path_params.add_argument('diaria_max', type=float)
path_params.add_argument('limit', type=float)
path_params.add_argument('offset', type=float)

class Hoteis(Resource):
    def get(self):

        connection = sqlite3.connect('banco.db')
        cursor = connection.cursor()

        dados = path_params.parse_args()
        dados_validos = {chave:dados[chave] for chave in dados if dados[chave] is not None}
        parametros = normalize_path_params_(**dados_validos)

        if not parametros.get('cidade'):
            
            tupla = tuple([parametros[chave] for chave in parametros])
            resultado = cursor.execute(consulta_sem_cidade, tupla)  

        else:
            tupla = tuple([parametros[chave] for chave in parametros])
            resultado = cursor.execute(consulta_com__cidade, tupla)  

        hoteis = []
        for linha in resultado:
            hoteis.append({
            'hotel_id': linha[0],
            'nome': linha[1],
            'estrelas': linha[2],
            'diaria': linha[3],
            'cidade': linha[4],
            'site_id': linha[5]
            })


        return{'hoteis': hoteis}

class Hotel(Resource):
    argumentos = reqparse.RequestParser()
    argumentos.add_argument('nome', type=str, required=True, help= "this field 'nome' cannot be left blank")
    argumentos.add_argument('estrelas', type=float, required=True, help= "this field 'estrelas' cannot be left blank")
    argumentos.add_argument('cidade')
    argumentos.add_argument('diaria')
    argumentos.add_argument('site_id', type=int, required=True, help="Every Hotel needs to be linked with a site ")


    def get(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            return hotel.json()
        return{'Message': 'Hotel not found'}, 404 # not found    

    @jwt_required()
    def post(self, hotel_id):
        if HotelModel.find_hotel(hotel_id):
            return {"mensage": f"hotel id '{hotel_id}' alredy exists."}, 400

        dados = Hotel.argumentos.parse_args()
        hotel = HotelModel(hotel_id, **dados)

        if not SiteModel.find_by_id(dados['site_id']):
            return {'message': 'The hotel must be associated to a valid site id'}, 400 # Se não tiver site id, mostrar seguinte mensagem...
        try:
            hotel.save_hotel()
        except:
            return {'message': 'an internal error ocurred trying to save hotel.'}, 500 #Internal server error
        return hotel.json()

    @jwt_required()
    def put(self, hotel_id):

        dados = Hotel.argumentos.parse_args()
        hotel_encontrado = HotelModel.find_hotel(hotel_id)
        
        if hotel_encontrado:
            hotel_encontrado.update_hotel(**dados)
            hotel_encontrado.save_hotel()
            return hotel_encontrado.json(), 200
        hotel = HotelModel(hotel_id, **dados)
        try:
            hotel.save_hotel()
        except:
            return {'message': 'an internal error ocurred trying to save hotel.'}, 500 #Internal server error
        return hotel.json(), 201

    @jwt_required()
    def delete(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            try:
                hotel.delete_hotel()
            except:
                return {'message': 'an internal error ocurred trying to delete hotel.'}, 500 #Internal server error
            return {'message': 'Hotel deleted.'}
        return {'message': 'Hotel not found'}, 404      