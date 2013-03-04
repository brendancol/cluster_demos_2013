import functools
from error_utils import reportSysErrors, reportArcpyErrors

try:
    from arcpy import ExecuteError, GetMessages
except ImportError:
    ExecuteError = None
    GetMessages = lambda c:'sorry no arcpy'

import sys
import traceback

def reportSysErrors(logger=None):
    '''
    reports python system related errors
    '''
    
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = "PYTHON ERRORS:\nTraceback Info:\n"
    pymsg += tbinfo + "\n"
    pymsg += "Error Info:\n" + str(sys.exc_type) + ": "
    pymsg += str(traceback.print_exc()) + "\n"

    if logger:
        logger.error(pymsg)
    else:
        print pymsg
    
    raise
    
def reportArcpyErrors(logger=None):
    message = "ArcPy ERRORS:\n" + GetMessages() + "\n"
    if logger:
        logger.error(message)
    else:
        print message
    raise

    pass
def decorator(declared_decorator):
    '''
    Decorator factory...
    '''
    @functools.wraps(declared_decorator)
    def final_decorator(func=None,**kwargs):
        def decorated(func):
            @functools.wraps(func)
            def wrapper(*a, **kw):
                return declared_decorator(func, a, kw, **kwargs)
            return wrapper
        if func is None:
            return decorated
        else:
            return decorated(func)
    return final_decorator

@decorator
def logArgs(func, func_args, func_kwargs, logger=None):
    arg_names = func.func_code.co_varnames[:func.func_code.co_argcount]
    args = func_args[:len(arg_names)]
    defaults = func.func_defaults or ()
    args = args + defaults[len(defaults) - (func.func_code.co_argcount - len(args)):]
    params = zip(arg_names, args)
    args = func_args[len(arg_names):]
    if args: params.append(('args', args))
    if func_kwargs: params.append(('kwargs', func_kwargs))
    logger.debug(func.func_name + ' (' + ', '.join('%s = %r' % p for p in params) + ' )')
    return func(*func_args, **func_kwargs)

@decorator
def standardErrorLoggging(func, func_args, func_kwargs, logger=None):
    try:
        return func(*func_args, **func_kwargs)
    except ExecuteError:
        reportArcpyErrors(logger)
        reportSysErrors(logger)
    except:
        reportSysErrors(logger)


#Testing...
def runLogArgsTest():
    from log_utils import createDefaultLogger
    logger = createDefaultLogger('test-decorator')
    
    @logArgs(logger=logger)
    def testLogArgs(x,y,z):
        pass
    
    testLogArgs(2,3,4)

def runStandardErrorLogggingTest():
    from log_utils import createDefaultLogger
    logger = createDefaultLogger('test-decorator')
    
    @standardErrorLoggging(logger=logger)
    def testStandardErrorLoggging(x,y,z):
        raise Exception('Testing Standard Error Logging')
    try:
        testStandardErrorLoggging(2,3,4)
    except:
        pass

if __name__ == '__main__':
    runLogArgsTest()
    runStandardErrorLogggingTest()
