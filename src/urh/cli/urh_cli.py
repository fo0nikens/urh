#!/usr/bin/env python3

import os
import sys
import argparse

cur_file = os.readlink(__file__) if os.path.islink(__file__) else __file__
cur_dir = os.path.realpath(os.path.dirname(cur_file))
sys.path.insert(0, os.path.realpath(os.path.join(cur_dir, "..", "..")))

from urh.dev.BackendHandler import BackendHandler
from urh.signalprocessing.Modulator import Modulator
from urh.dev.VirtualDevice import VirtualDevice

DEVICES = BackendHandler.DEVICE_NAMES
MODULATIONS = Modulator.MODULATION_TYPES
PAUSE_SEP = "/"


def build_modulator_from_args(arguments: argparse.Namespace):
    if arguments.raw:
        return None

    if arguments.parameter_zero is None:
        raise ValueError("You need to give a modulation parameter for zero (-p0, --parameter-zero)")

    if arguments.parameter_one is None:
        raise ValueError("You need to give a modulation parameter for one (-p1, --parameter-one)")

    result = Modulator("CLI Modulator")
    result.carrier_freq_hz = arguments.carrier_frequency
    result.carrier_amplitude = arguments.carrier_amplitude
    result.samples_per_bit = arguments.bit_length
    result.param_for_zero = arguments.parameter_zero
    result.param_for_one = arguments.parameter_one
    result.modulation_type_str = arguments.modulation_type
    result.sample_rate = arguments.sample_rate

    return result


def build_device_from_args(arguments: argparse.Namespace):
    from urh.dev.VirtualDevice import Mode
    from urh.dev.BackendHandler import Backends
    if arguments.receive and arguments.transmit:
        raise ValueError("You cannot use receive and transmit mode at the same time.")
    if not arguments.receive and not arguments.transmit:
        raise ValueError("You must choose a mode either RX (-rx, --receive) or TX (-tx, --transmit)")

    bh = BackendHandler()
    if arguments.device_backend == "native":
        bh.device_backends[arguments.device.lower()].selected_backend = Backends.native
    elif arguments.device_backend == "gnuradio":
        bh.device_backends[arguments.device.lower()].selected_backend = Backends.grc
    else:
        raise ValueError("Unsupported device backend")

    bandwidth = arguments.sample_rate if arguments.bandwidth is None else arguments.bandwidth
    result = VirtualDevice(bh, name=arguments.device, mode=Mode.receive if arguments.receive else Mode.send,
                           freq=arguments.frequency, sample_rate=arguments.sample_rate,
                           bandwidth=bandwidth,
                           gain=arguments.gain, if_gain=arguments.if_gain, baseband_gain=arguments.baseband_gain)

    return result


parser = argparse.ArgumentParser(description='This is the Command Line Interface for the Universal Radio Hacker.',
                                 add_help=False)

group1 = parser.add_argument_group('Software Defined Radio Settings', "Configure Software Defined Radio options")
group1.add_argument("-d", "--device", required=True, choices=DEVICES, metavar="DEVICE",
                    help="Choose a Software Defined Radio. Allowed values are " + ", ".join(DEVICES))
group1.add_argument("-di", "--device-identifier")
group1.add_argument("-db", "--device-backend", choices=["native", "gnuradio"], default="native")
group1.add_argument("-f", "--frequency", type=float, required=True, help="Center frequency the SDR shall be tuned to")
group1.add_argument("-s", "--sample-rate", type=float, required=True, help="Sample rate to use")
group1.add_argument("-b", "--bandwidth", type=float, help="Bandwidth to use (defaults to sample rate)")
group1.add_argument("-g", "--gain", type=int, help="RF gain the SDR shall use")
group1.add_argument("-i", "--if-gain", type=int, help="IF gain to use (only supported for some SDRs)")
group1.add_argument("-bb", "--baseband-gain", type=int, help="Baseband gain to use (only supported for some SDRs)")

group2 = parser.add_argument_group('Modulation/Demodulation settings',
                                   "Configure the Modulator/Demodulator. Not required in raw mode."
                                   "In case of RX there are additional demodulation options.")
group2.add_argument("-cf", "--carrier-frequency", type=float, default=1e3,
                    help="Carrier frequency in Hertz (default: %(default)s)")
group2.add_argument("-ca", "--carrier-amplitude", type=float, default=1,
                    help="Carrier amplitude (default: %(default)s)")
group2.add_argument("-cp", "--carrier-phase", type=float, default=0,
                    help="Carrier phase in degree (default: %(default)s)")
group2.add_argument("-mo", "--modulation-type", choices=MODULATIONS, metavar="MOD_TYPE", default="FSK",
                    help="Modulation type must be one of " + ", ".join(MODULATIONS) + " (default: %(default)s)")
group2.add_argument("-p0", "--parameter-zero", help="Modulation parameter for zero")
group2.add_argument("-p1", "--parameter-one", help="Modulation parameter for one")

group2.add_argument("-n", "--noise", type=float, default=0.1,
                    help="Noise threshold (default: %(default)s). Used for RX only.")
group2.add_argument("-c", "--center", type=float, default=0,
                    help="Center between 0 and 1 for demodulation (default: %(default)s). Used for RX only.")
group2.add_argument("-bl", "--bit-length", type=float, default=100,
                    help="Length of a bit in samples (default: %(default)s). Used for RX only.")
group2.add_argument("-t", "--tolerance", type=float, default=5,
                    help="Tolerance for demodulation in samples (default: %(default)s). Used for RX only.")

group3 = parser.add_argument_group('Data configuration', "Configure which data to send or where to receive it.")
group3.add_argument("--hex", action='store_true', help="Give messages as hex instead of bits")
group3.add_argument("-m", "--messages", nargs='+', help="Messages to send. Give pauses after with a {0}. "
                                                        "Separate with spaces e.g. "
                                                        "1001{0}42ms 1100{0}3ns 0001 1111{0}200. "
                                                        "If you give no time suffix "
                                                        "after a pause it is assumed to be in samples. "
                                                        "You can also give a path to a file from where "
                                                        "to read the messages from. "
                                                        "If you give a file here in RX mode received messages will "
                                                        "be written to this file instead to STDOUT.".format(PAUSE_SEP))
group3.add_argument("-p", "--pause", default="250ms",
                    help="The default pause which is inserted after a every message "
                         "which does not have a pause configured. (default: %(default)s) "
                         "Supported time units: s (second), ms (millisecond), ns (nanosecond) "
                         "If you do not give a time suffix the pause is assumed to be in samples.")
group3.add_argument("-rx", "--receive", action="store_true", help="Enter RX mode")
group3.add_argument("-tx", "--transmit", action="store_true", help="Enter TX mode")
group3.add_argument("-r", "--raw", action="store_true", help="Use raw mode i.e. send/receive IQ data instead of bits.")

group4 = parser.add_argument_group("Miscellaneous options")
group4.add_argument("-h", "--help", action="help", help="show this help message and exit")
group4.add_argument("-v", "--verbose", action="store_true")

args = parser.parse_args()
try:
    modulator = build_modulator_from_args(args)
    device = build_device_from_args(args)
except Exception as e:
    print(e)
    sys.exit(1)
