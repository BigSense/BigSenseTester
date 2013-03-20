#!/usr/bin/env python3

from greentest.loader import load_config, get_class
from greentest.test import  TestSet, AbstractTest
from optparse import OptionParser, OptionGroup
import logging
from datetime import datetime
from sys import argv
from sys import exit

def logfile_arg():
  def func(option,opt_str,value,parser):
    if parser.rargs and not parser.rargs[0].startswith('-'):
      val=parser.rargs[0]
      parser.rargs.pop(0)
    else:
      #defaults to program_name_YYYY-MM-DD_HHMMSS.log
      val = argv[0] + '_' + datetime.now().strftime('%Y-%m-%d_%H%M%S') + '.log'
      setattr(parser.values,option.dest,val)
  return func


if __name__ == '__main__':
  parser = OptionParser(usage="%prog [-t] [-l logfile] [-v (debug,info,warn,error)] <testset>",
                        description="A script for running automated functional tests against the GreenOven Web Service",
                        version="%prog 0.1", epilog='Copyright 2011 Sumit Khanna. GNU GPLv3. PenguinDreams.org')
  parser.add_option('-t','--trace',action='store_true',dest='trace',help='Display all request and response information for each test')
  loggingOpts = OptionGroup(parser,'Logging Options')
  loggingOpts.add_option('-l','--logfile',action='callback',callback=logfile_arg(),help='store output to logfile [default: {0}_yyyy-mm-dd-hhmmss.log]'.format(argv[0]),metavar='FILE',dest='logfile')
  loggingOpts.add_option('-v','--level',type='string',help='log level: trace,debug,info,error [default: info]',metavar='level',default='info')
  parser.add_option_group(loggingOpts)

  (options, args) = parser.parse_args()

  if len(args) != 1:
    parser.error('You must specify a test set')
  else:

    #-l option
    if options.level.upper() in ['DEBUG','INFO','WARN','ERROR']:
      lvl = getattr(logging, options.level.upper())
      logging.getLogger('').setLevel(lvl)
    else:
      parser.error('Invalid log level: {1}'.format(options.level))

      #logger setup
      #if options.verbose is True:
      #  console = logging.StreamHandler()
      #  console.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
      #  logging.getLogger('').addHandler(console)

    if options.logfile is not None:
      logfile = logging.FileHandler(options.logfile)
      logfile.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s'))
      logging.getLogger('').addHandler(logfile)


    load_config()
    set = get_class(args[0])
    set.trace = options.trace

    #hack for running single test
    if isinstance(set,AbstractTest):
      single = TestSet()
      single.name = 'Single Test'
      single.trace = options.trace
      single.tests = [ set ]
      set = single

    if not set.run_tests():
      exit(2)
