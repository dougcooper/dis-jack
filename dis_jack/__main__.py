import argparse
import asyncio
from dis_jack.utils import select
from dis_jack.virt_radio import VirtualRadio
from dis_jack.jack_interface import JackInterface
from dis_jack.udp_interface import UdpInterface

parser = argparse.ArgumentParser()
parser.add_argument('-n','--name',type=str,default='dis-jack',required=False)
parser.add_argument('-s','--server',type=str,default='jack',required=False)
parser.add_argument('-a','--autoconnect',action='store_true',default=False,required=False)
parser.add_argument('--ip',type=str,default='127.0.0.1')
parser.add_argument('--port',type=int,default=6993)
args = parser.parse_args()

# jack = JackInterface(args.name,args.server)
jack = JackInterface(args.name)
udp = UdpInterface()
radio = VirtualRadio(jack,udp)

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
    with jack(args.autoconnect):      
        print('Press Ctrl+C to stop')
        try:
            asyncio.run(main())
            print("Exiting...")
        except KeyboardInterrupt:
            print('\nInterrupted by user')