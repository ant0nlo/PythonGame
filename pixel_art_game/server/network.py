import socket
import threading
import json
import time
import uuid
from .game_state import game_state
from .config import HOST, PORT, MAX_CLIENTS, UPDATE_INTERVAL

clients = []

def broadcast(message):
    """Safe broadcast with error handling"""
    #print(f"Broadcasting message: {message}")

    disconnected = []
    for client in clients:
        try:
            client.sendall((message + "\n").encode())
        except Exception as e:
            print(f"Broadcast error to {client}: {e}")
            disconnected.append(client)
    
    for client in disconnected:
        if client in clients:
            clients.remove(client)
            try:
                client.close()
            except Exception as ex:
                print(f"Error closing client socket: {ex}")

def client_handler(client_socket, address):
    player_id = str(uuid.uuid4())
    print(f"Client {player_id} connected from {address}")

    try:
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            
            messages = data.decode().split('\n')
            for msg in messages:
                if msg.strip():
                    try:
                        message = json.loads(msg.strip())
                        handle_message(client_socket, player_id, message)
                    except json.JSONDecodeError:
                        print(f"Invalid JSON from {player_id}: {msg}")
            
    except Exception as e:
        print(f"Connection error with {player_id}: {e}")
    finally:
        game_state.remove_player(player_id)
        if client_socket in clients:
            clients.remove(client_socket)
        client_socket.close()
        print(f"Client {player_id} disconnected")

def handle_message(client_socket, player_id, message):
    message_type = message.get("type")
    data = message.get("data", {})

    if message_type == "join_ack":
            client_socket.sendall(json.dumps({
                "type": "map_data",
                "data": game_state.map
            }).encode() + b"\n")

    if message_type == "join":
        name = data.get("name", "Anonymous")
        avatar = data.get("avatar", "Default")
        hero_class = data.get("hero_class", "warrior")
        game_state.add_player(player_id, name, avatar, hero_class=hero_class)
        client_socket.sendall(json.dumps({
            "type": "join_ack",
            "data": {"player_id": player_id}
        }).encode() + b"\n")

    if message_type == "attack_enemy":
        enemy_id = data.get("enemy_id")
        damage = data.get("damage", 10)
        
        if game_state.handle_enemy_attack(player_id, enemy_id, damage):
            client_socket.sendall(json.dumps({
                "type": "attack_result",
                "data": {
                    "success": True, 
                    "enemy_id": enemy_id
                }
            }).encode() + b"\n")
        else:
            client_socket.sendall(json.dumps({
                "type": "attack_result",
                "data": {
                    "success": False, 
                    "message": "Attack failed"
                }
            }).encode() + b"\n")

    if message_type == "player_death":
        print("Massage about dead:", data)
        if data.get("player_id") == player_id:
            print("You have died! Game over.")
        
    elif message_type == "move":
        direction = data.get("direction")
        speed = data.get("speed", 5)
        dx, dy = 0, 0
        if direction == "up":
            dy = -speed
        elif direction == "down":
            dy = speed
        elif direction == "left":
            dx = -speed
        elif direction == "right":
            dx = speed
        game_state.move_player(player_id, dx, dy)
        
    elif message_type == "leave":
        game_state.remove_player(player_id)
        
    elif message_type == "pickup":
        item_id = data.get("item_id")
        if game_state.pickup_item(player_id, item_id):
            item_type = game_state.get_picked_item_type(player_id, item_id)
            client_socket.sendall(json.dumps({
                "type": "pickup_result",
                "data": {"success": True, "item_type": item_type}
            }).encode() + b"\n")
        else:
            client_socket.sendall(json.dumps({
                "type": "pickup_result",
                "data": {"success": False}
            }).encode() + b"\n")
            
    elif message_type == "drop":
        item_index = data.get("item_index")
        if game_state.drop_item(player_id, item_index):
            client_socket.sendall(json.dumps({
                "type": "drop_result",
                "data": {"success": True}
            }).encode() + b"\n")
        else:
            client_socket.sendall(json.dumps({
                "type": "drop_result",
                "data": {"success": False}
            }).encode() + b"\n")   

    elif message_type == "use_item":
            item_type = data.get("item_type")
            if item_type == "potion":
                heal_amount = data.get("heal_amount", 25)
                new_health = game_state.heal_player(player_id, heal_amount)
                
                if new_health is not None:
                    client_socket.sendall(json.dumps({
                        "type": "health_update",
                        "data": {
                            "player_id": player_id,
                            "health": new_health,
                            "source": "heal"
                        }
                    }).encode() + b"\n") 

            elif item_type == "mana_potion": 
                    mana_amount = data.get("mana_amount", 25)
                    new_mana = game_state.add_mana(player_id, mana_amount)
                    
                    if new_mana is not None:
                        client_socket.sendall(json.dumps({
                            "type": "mana_update",
                            "data": {
                                "player_id": player_id,
                                "mana": new_mana
                            }
                        }).encode() + b"\n")

    elif message_type == "use_special":
            ability_data = message.get("data", {})
            result = game_state.use_special_ability(player_id, ability_data)
            
            client_socket.sendall(json.dumps({
                "type": "special_result",
                "data": result
            }).encode() + b"\n")

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(MAX_CLIENTS)
    print(f"Server listening on {HOST}:{PORT}")
    threading.Thread(target=update_loop, daemon=True).start()
    while True:
        client_socket, address = server_socket.accept()
        clients.append(client_socket)
        threading.Thread(target=client_handler, args=(client_socket, address), daemon=True).start()

def update_loop():
    while True:
        game_state.update_enemies()
        game_state.update_effects()
        state = game_state.get_state()
        message = json.dumps({"type": "update_state", "data": state})
        broadcast(message)
        time.sleep(UPDATE_INTERVAL)