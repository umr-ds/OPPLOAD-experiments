''' DTN-RPyC service
'''

import os

from core.service import CoreService
from core.service import ServiceManager


class DTNRPyCService(CoreService):
    '''
    Remote Procedure Calls for Delay-Tolerant Networking
    '''
    # a unique name is required, without spaces
    _name = "DTN-RPyC"
    # you can create your own group here
    _group = "Utility"
    # list of other services this service depends on
    _depends = ("Serval")
    # per-node directories
    _dirs = ()
    # generated files (without a full path this file goes in the node's dir,
    #  e.g. /tmp/pycore.12345/n1.conf/)
    _configs = ()
    # this controls the starting order vs other enabled services
    _startindex = 40
    # list of startup commands, also may be generated during startup
    _startup = (
        'bash -c "cp -r /shared/dtnrpc_configs/* ."',
    )
    # list of shutdown commands
    _shutdown = ()

    @classmethod
    def generateconfig(cls, node, filename, services):
        ''' Return a string that will be written to filename, or sent to the
            GUI for user customization.
        '''




def load_services():
    ServiceManager.add(DTNRPyCService)
