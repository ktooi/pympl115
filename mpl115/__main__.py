# -*- coding: utf-8 -*-
from __future__ import print_function
from argparse import ArgumentParser
import json
from logging import basicConfig, getLogger, DEBUG, INFO
from . import MPL115


# これはメインのファイルにのみ書く
basicConfig(level=INFO)
logger = getLogger(__name__)


def measure(mpl115, args):
    mpl115.measure()
    mpl115.read()
    if not args.quick:
        mpl115.measure()


def temperature(mpl115, args):
    measure(mpl115, args)
    print(mpl115.temperature)


def humidity(mpl115, args):
    measure(mpl115, args)
    print(mpl115.humidity)


def discomfort(mpl115, args):
    measure(mpl115, args)
    print(mpl115.discomfort)


def default(mpl115, args):
    print("temperature : {temp}".format(temp=mpl115.temperature))
    print("humidity    : {hum}".format(hum=mpl115.humidity))
    print("discomfort  : {dscf}".format(dscf=mpl115.discomfort))


def to_json(mpl115, args):
    mesg = json.dumps({"temperature": mpl115.temperature,
                       "humidity": mpl115.humidity,
                       "discomfort": mpl115.discomfort})
    print(mesg)


def parse_args():
    parser = ArgumentParser(description=("Measure and show atmospheric pressure from MPL115a2.")
    parser.add_argument('-d', '--debug', action='store_true', help="Show verbose messages.")
    parser.add_argument('-b', '--bus', dest="bus", type=int, default=1, help="Bus number.")
    parser.add_argument('-q', '--quick', dest="quick", action='store_true',
                        help="Quickly response mode. The response will be faster, but the output data will be outdated.")
    parser.set_defaults(func=default, subcommand="default")
    subparsers = parser.add_subparsers(dest="subcommand")

    # 共通となる引数を定義。
    common_parser = ArgumentParser(add_help=False)
    common_parser.add_argument('--unit', '-u', action='store_true', help="")

    subcmd_temp = subparsers.add_parser("temperature", parents=[common_parser], help="Output temperature.")
    subcmd_temp.set_defaults(func=temperature)

    subcmd_hum = subparsers.add_parser("humidity", parents=[common_parser], help="Output humidity.")
    subcmd_hum.set_defaults(func=humidity)

    subcmd_disc = subparsers.add_parser("discomfort", parents=[common_parser],
                                        help="Output discomfort that calculated with temperature and humidity.")
    subcmd_disc.set_defaults(func=discomfort)

    subcmd_json = subparsers.add_parser("json", parents=[common_parser],
                                        help="Output data that temperature, humidity and discomfort within JSON format.")
    subcmd_json.set_defaults(func=to_json)

    # 以下、ヘルプコマンドの定義。

    # "help" 以外の subcommand のリストを保持する。
    # dict.keys() メソッドは list や tuple ではなく KeyView オブジェクトを戻す。
    # これは、対象となる dict の要素が変更されたときに、 KeyView オブジェクトの内容も変化してしまうので、
    # subparsers.choices の変更が反映されないように list 化したものを subcmd_list に代入しておく。
    subcmd_list = list(subparsers.choices.keys())

    # この行は `subcmd_list` のリスト作成より後に実行しなければならない。
    # この順番を守らないと、 `subcmd_list` に "help" が含まれてしまう。
    subcmd_help = subparsers.add_parser("help", help="Help is shown.")

    # add_argument() の第一引数を "subcommand" としてはならない。
    # `mcbdsc help build` 等と実行した際に、
    # >>> args = parser.parse_args()
    # >>> args.subcommand
    # で "help" となってほしいが、この第一引数を "subcommand" にしてしまうとこの例では "build" となってしまう。
    # このため、ここでは第一引数を "subcmd" とし、 metavar="subcommand" とすることで
    # ヘルプ表示上は "subcommand" としたまま、 `args.subcommand` が "help" となるよう対応する。
    subcmd_help.add_argument("subcmd", metavar="subcommand", choices=subcmd_list, help="Command name which help is shown.")

    args = parser.parse_args()

    if args.subcommand == "help":
        # ヘルプを表示して終了。
        parser.parse_args([args.subcmd, '--help'])
    
    return args


def main():
    args = parse_args()
    if args.debug:
        logger.info("Set loglevel to debug.")
        logger.setLevel(DEBUG)
    mpl115 = MPL115(name="mpl115", bus=args.bus)
    args.func(mpl115, args)
