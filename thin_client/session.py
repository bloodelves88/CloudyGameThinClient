import os
import struct
import socket
import logging
import json
import settings

class GameSession(object):
    """
    Keyboard:
    8bit Version (Currently use 0)
    8bit Protocol Type : (Keyboard (1), Mouse (2), Gamepad, etc.)
    8bit ControllerID (start from 0)
    16bit UEKeyCode (A, B, , Z, 0, ... ,9, punctuation, etc.)
    16bit UECharCode (F1, ..., F12, Ctrl, Alt, Numpad, etc.)
    8bit Event (Key Down (2), Key Up (3))

    Mouse:
    8bit Version (Currently use 0)
    8bit Protocol Type : (Keyboard (1), Mouse (2), Gamepad, etc.)
    8bit ControllerID (start from 0)
    16bit x-axis movement
    16bit y-axis movement
    32bit x-axis position
    32bit y-axis position
    """

    def __init__(self, ip_address, player_controller_id):
        self.sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
        self.sock.setblocking(False)
        self.ip_address = socket.gethostbyname(ip_address)
        self.player_controller_id = player_controller_id
    
    def pack_and_send(self, device_type, ue_key_code, 
                      ue_char_code, event_type, pos_x=0, pos_y=0):
        """Packs the keyboard or mouse information into a UDP packet, 
           and sends it to the game (Remote Controller module)
        """
        data_keyboard = (settings.VERSION, device_type, self.player_controller_id,
                         ue_key_code, ue_char_code, event_type)
        data_mouse = (settings.VERSION, device_type, self.player_controller_id, 
                      ue_key_code, ue_char_code, pos_x, pos_y)
        if (device_type == settings.DEVICE_KEYBOARD):
            message = struct.pack(settings.PACKET_FORMAT_KEY, *data_keyboard)
        elif (device_type == settings.DEVICE_MOUSE):
            message = struct.pack(settings.PACKET_FORMAT_MOUSE, *data_mouse)
        #if (self.player_controller_id == 0):
        self.sock.sendto(message, (self.ip_address, settings.UDP_PORT))
        # These will not work since the player controller ID should always be 0 on the receiving end
        #elif (self.player_controller_id == 1):
        #    self.sock.sendto(message, (self.ip_address, 55565))
        #elif (self.player_controller_id == 2):
        #    self.sock.sendto(message, (self.ip_address, 55575))
        #elif (self.player_controller_id == 3):
        #    self.sock.sendto(message, (self.ip_address, 55585))

    def send_quit_command(self):
        """Sends a quit command to the game engine (CloudyPlayerManager module)"""
        json_data = {
           "command" : "quit",
           "controller" : self.player_controller_id
        }
        quit_command = json.dumps(json_data)
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((self.ip_address, settings.TCP_STREAMING_PORT))
            tcp_socket.sendall(quit_command.encode("utf-8"))
        except socket.error as error:
            logging.warning(os.strerror(error.errno));
        finally:
            tcp_socket.close()
            
    def send_join_command(self, ip, port, player_controller_id, session_id, game_id, username):
        json_data = {
           "command" : "join",
           "controller" : player_controller_id,
           "streaming_port" : port,
           "streaming_ip" : ip,
           "game_id" : game_id,
           "username" : username, 
           "game_session_id" : session_id,
        }
        join_command = json.dumps(json_data)
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((self.ip_address, settings.TCP_STREAMING_PORT))
            tcp_socket.sendall(join_command.encode("utf-8"))
        except socket.error as error:
            logging.warning(os.strerror(error.errno));
        finally:
            tcp_socket.close()
