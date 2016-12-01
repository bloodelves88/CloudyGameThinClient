import time
import argparse
import subprocess

def main(num_players, ip, *args, **kwargs):  
    for x in range(0, num_players):
        port = 30000 + x
        command = "python main.py {} {} {}".format(ip, port, x)
        subprocess.Popen(command)
        time.sleep(6) # Give some time to start up and start streaming

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Launch multiple thin clients with their configurations set up')
    parser.add_argument('num_players', metavar='num_players', type=int, default=1,
                        choices=range(1, 13),
                        help="Number of thin clients to launch. Value from 1 to 6.")
    parser.add_argument('ip', metavar='ip', type=str, default="127.0.0.1",
                        help="IP address to obtain video stream from")

    args = parser.parse_args()
    main(args.num_players, args.ip)