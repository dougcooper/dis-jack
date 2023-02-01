import argparse
import asyncio
import time
import os
from signal import SIGINT, SIGTERM
from dis_jack.audio_recorder import AudioRecorder, AudioWriterExecutor
from dis_jack.utils import select
from dis_jack.virt_radio import VirtualRadio
from dis_jack.jack_interface import JackInterface, Direction
from dis_jack.udp_interface import UdpInterface

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--name', type=str,
                    default='dis_jack', required=False)
parser.add_argument('-s', '--server', type=str, default='jack', required=False)
parser.add_argument('-a', '--auto',
                    action='store_true', default=False, required=False)
parser.add_argument('--ip', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=6993)
parser.add_argument('-d', '--dir', type=Direction, choices=list(Direction),action='append')
parser.add_argument('--dump', action='store_true',
                    default=False, required=False)
# TODO: add dis frequency
args = parser.parse_args()

# jack = JackInterface(args.name,args.server)
jack = JackInterface(args.name, auto_connect=args.auto, dir=args.dir)
udp = UdpInterface()

t = time.time()
cwd = os.getcwd()
writer = AudioWriterExecutor({
        "dis_out": AudioRecorder(f'dis_{t}', cwd, 8000), 
        "audio_out": AudioRecorder(f'audio_{t}', cwd, 48000)
        }) if args.dump else None
if writer:
    radio = VirtualRadio(jack, udp, writer)
else:
    radio = VirtualRadio(jack, udp)


async def main():
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: udp,
        local_addr=(args.ip, args.port)
    )
    coros = [
        udp.process(),
        radio.process(),
        jack.shutdown.wait()
    ]
    await select(coros)
    transport.close()

if __name__ == "__main__":
    with jack as client:
        print('Press Ctrl+C to stop')
        try:
            asyncio.run(main())
            print("Exiting...")
        except KeyboardInterrupt:
            print('\nInterrupted by user')
