import sys
import os
sys.path.append(os.path.dirname(os.getcwd()))
sys.path.append(os.getcwd())
import logging
import pygame
import argparse
import time
from random import randint
from pygame.locals import *
from thin_client.session import GameSession
from thin_client import settings
from thin_client import stream_reader


class Action:
    def __init__(self, session, pygame):
        self.session = session
        self.pygame = pygame

    def process(self, event):
        """Do Nothing by default"""
        pass
    
class MouseMotionRandom(Action):
    def process(self, event):
        """Processes mouse motion events and sends it to the pack_and_send method"""
        self.session.pack_and_send(settings.DEVICE_MOUSE, randint(-15,15), randint(-15,15), event.type)

class MouseMotionRandom1(Action):
    def process(self, event):
        """Processes mouse motion events and sends it to the pack_and_send method"""
        self.session.pack_and_send(settings.DEVICE_MOUSE, randint(-10,5), randint(-5,5), event.type)
        
class MouseButton(Action):
    def process(self, event):
        """Processes mouse button events and sends it to the pack_and_send method"""
        left_mouse_button, middle_mouse_button, right_mouse_button = self.pygame.mouse.get_pressed()
        if (left_mouse_button == 1):
            ue_char_code = 1
        elif (middle_mouse_button == 1):
            ue_char_code = 4
        elif (right_mouse_button == 1):
            ue_char_code = 2
        else:
            ue_char_code = 0
        ue_key_code = ue_char_code
        if (event.type == MOUSEBUTTONDOWN):
            self.session.pack_and_send(settings.DEVICE_KEYBOARD,
                ue_key_code, ue_char_code, 2)
        elif (event.type == MOUSEBUTTONUP):
            self.session.pack_and_send(settings.DEVICE_KEYBOARD,
                ue_key_code, ue_char_code, 3)
        logging.info("Mouse button: %s => %s", self.pygame.mouse.get_pressed(), ue_key_code)


class MouseMotion(Action):
    def process(self, event):
        """Processes mouse motion events and sends it to the pack_and_send method"""
        x, y = self.pygame.mouse.get_rel()
        self.session.pack_and_send(settings.DEVICE_MOUSE, x, y, event.type)
        logging.info("Mouse motion: %d %d", x, y)


class KeyboardButton(Action):
    def process(self, event):
        """Processes keyboard button events and sends it to the pack_and_send method"""
        ue_key_code = settings.ASCII_TO_UE_KEYCODE.get(event.key, 0)
        ue_char_code = settings.ASCII_TO_UE_CHARCODE.get(event.key, ue_key_code)
        ue_key_code = ue_char_code or ue_key_code # This code is redundant. It changes nothing.
        self.session.pack_and_send(settings.DEVICE_KEYBOARD, 
            ue_key_code, ue_char_code, event.type)

        logging.info("Keyboard: %s => %s", event.key, ue_key_code)

class QuitAction(Action):
    def process(self, event):
        """Call the send_quit_command method when the user closes the thin client"""
        self.session.send_quit_command()
        
def initialize_pygame(fps):
    """Initialize pygame with the window size, mouse settings, etc.
    
    Keyword arguments:
    fps -- the rate pygame will read key events at
    """
    pygame.init()
    screen = pygame.display.set_mode((settings.RESO_WIDTH, settings.RESO_HEIGHT))
    pygame.display.set_caption(settings.TEXT_WINDOW_TITLE)
    pygame.mouse.set_visible(False) # Makes mouse invisible
    pygame.event.set_grab(True) # confines the mouse cursor to the window
    frame_interval = int((1/fps)*1000)
    pygame.key.set_repeat(frame_interval, frame_interval) # 1 input per frame

    show_message(screen, settings.TEXT_LOADING, settings.TEXT_PATIENCE)

    return screen

def show_message(screen, line1, line2, line3=settings.TEXT_INSTRUCTIONS):
    """Shows a message consisting of 3 lines on the screen.
    
    Keyword arguments:
    screen -- the pygame screen object
    line1 -- first line of the message
    line2 -- second line of the message
    line3 -- third line of the message, appears significantly lower on the screen 
             (default: shows thin client lock/unlock mouse instructions)
    """
    
    screen.fill(settings.SCREEN_BACKGROUND_COLOR)
    main_font = pygame.font.Font(None, settings.TEXT_MAIN_FONT_SIZE)
    small_font = pygame.font.Font(None, settings.TEXT_SMALL_FONT_SIZE)
    line1_message = main_font.render(line1, True, settings.TEXT_COLOUR)
    line2_message = main_font.render(line2, True, settings.TEXT_COLOUR)
    line3_message = small_font.render(line3, True, settings.TEXT_COLOUR)
    line1_text_rect = line1_message.get_rect()
    line2_text_rect = line2_message.get_rect()
    line3_text_rect = line3_message.get_rect()
    line1_pos_x = screen.get_rect().centerx - line1_text_rect.centerx
    line1_pos_y = screen.get_rect().centery - line1_text_rect.centery
    line2_pos_x = screen.get_rect().centerx - line2_text_rect.centerx
    line3_pos_x = screen.get_rect().centerx - line3_text_rect.centerx
    screen.blit(line1_message, (line1_pos_x, line1_pos_y - 50))
    screen.blit(line2_message, (line2_pos_x, line1_pos_y))
    screen.blit(line3_message, (line3_pos_x, line1_pos_y + 125))
    pygame.display.update()

    return screen

def toggle_mouse_grab(pygame, is_mouse_grabbed):
    """Toggles mouse grab. Mouse grab is when the mouse is locked to the interior of the window.
    
    Keyword arguments:
    pygame -- the pygame object
    is_mouse_grabbed -- a boolean value 
    """
    if (is_mouse_grabbed == True):
        is_mouse_grabbed = False
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)
    else:
        is_mouse_grabbed = True
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)

    return is_mouse_grabbed

def start_client(ip, port, player_controller_id, *args, **kwargs):
    """Main event loop starts here. Calls all methods to initialze the GameSession, video streaming,
    and pygame.
    
    Keyword arguments:
    ip -- IP address to read the video broadcast from
    port -- Port of the IP address to read the video broadcast from
    player_controller_id -- The player controller ID of the user using this thin client
    """
    session = GameSession(ip, player_controller_id)
    screen = initialize_pygame(settings.FPS)
    scale, offset, is_width_smaller, capture_object = stream_reader.setup_stream(ip, port)
    is_running = True
    is_mouse_grabbed = True

    while (is_running):
        image_frame = stream_reader.get_frame(capture_object, scale)
        event = pygame.event.poll()

        # If we did not manage to get a frame from the stream
        if (image_frame == False):
            show_message(screen, settings.TEXT_SERVER_DISCONNECTED, settings.TEXT_RESTART_CLIENT)
            action = Action(session, pygame)
            
        else:
            if (player_controller_id == 0):
                action = MouseMotionRandom(session, pygame)
            elif (player_controller_id == 1):
                action = MouseMotionRandom(session, pygame)
            elif (player_controller_id == 2):
                action = MouseMotionRandom(session, pygame)
            elif (player_controller_id == 3):
                action = MouseMotionRandom1(session, pygame)
            elif (player_controller_id == 4):
                action = MouseMotionRandom1(session, pygame)
            elif (player_controller_id == 5):
                action = MouseMotionRandom1(session, pygame)
            else:
                action = MouseMotionRandom(session, pygame)

            '''
            elif (event.type == KEYDOWN or event.type == KEYUP):
                action = KeyboardButton(session, pygame)                    
            elif (event.type == pygame.MOUSEMOTION):
                action = MouseMotion(session, pygame)
            elif (event.type == MOUSEBUTTONDOWN or event.type == MOUSEBUTTONUP):
                action = MouseButton(session, pygame)
            '''
                
            # Display the frame on the pygame window
            if (is_width_smaller):
                screen.blit(image_frame, (0, offset))
            else:
                screen.blit(image_frame, (offset, 0))
            pygame.display.flip()
            
        # To toggle mouse grabbing within the window
        if (event.type == KEYUP and event.key == K_ESCAPE):
            is_mouse_grabbed = toggle_mouse_grab(pygame, is_mouse_grabbed)
        elif (event.type == QUIT):
            action = QuitAction(session, pygame)
            is_running = False
            capture_object.release()

        action.process(event)

    pygame.quit()

def main(ip, port, player_controller_id, session_id, game_id, username, *args, **kwargs):
    session = GameSession(ip, player_controller_id)
    session.send_join_command(ip, port, player_controller_id, session_id, game_id, username)
    
    print("Thin client starting with ip {}, port {}, player controller id {}".format(ip, port, player_controller_id))
    
    time.sleep(5) # Give ffmpeg some time to start up and start streaming
    start_client(ip, port, int(player_controller_id), *args, **kwargs)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Launch the thin client.')
    parser.add_argument('ip', metavar='ip', type=str, default="127.0.0.1",
                        help="IP address to obtain video stream from")
    parser.add_argument('port', metavar='port', type=int, default=30000,
                        choices=range(30000, 30006),
                        help="Port of the IP address you are connecting to. Value from 30000 to 30005")
    parser.add_argument('player', metavar='player', type=int, default=0,
                        choices=range(0, 6),
                        help="Player controller ID of the player. Value from 0 to 5.")
    parser.add_argument('--session', metavar='session', type=int, default=1,
                        help="ID of the current game session being used.")
    parser.add_argument('--gameid', metavar='gameid', type=int, default=1,
                        help="ID of the current game being played.")
    parser.add_argument('--username', metavar='username', type=str, default="dummy",
                        help="Username of the player playing.")

    args = parser.parse_args()
    main(args.ip, args.port, args.player, args.session, args.gameid, args.username)
