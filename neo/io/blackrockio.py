# -*- coding: utf-8 -*-

from neo.io.basefromrawio import BaseFromRaw
from neo.rawio.blackrockrawio import BlackrockRawIO

class BlackrockIO():
    name = 'Blackrock IO'
    description = "This IO reads .nev/.nsX file of the Blackrock " + \
        "(Cerebus) recordings system."
    
    _prefered_signal_group_mode = 'split-all'

    _instances = {}

    def __init__(self, filename, nsx_to_load=[None], **kargs):
        for nsx_val in nsx_to_load:
            self._instances[nsx_val] = (self.SingleBlackrockIO(filename, nsx_val, **kargs))

    def read_block(self, block_index=0, lazy=False, cascade=True, signal_group_mode=None,
                units_group_mode=None, load_waveforms=False, time_slices=None, nsx_to_load=None):

        if nsx_to_load is None:
            return None
        elif isinstance(nsx_to_load, int):
            nsx_to_load = [nsx_to_load]
        elif nsx_to_load == 'all':
            nsx_to_load = list(self._instances)
        elif not isinstance(nsx_to_load, list):
            raise ValueError("nsx_to_load should be 'all' or of type int or list")

        all_blocks = []
        for nsx_val in nsx_to_load:
            all_blocks.append(self._instances[nsx_val].read_block(block_index=block_index, lazy=lazy, cascade=cascade,
                                                       signal_group_mode=signal_group_mode,
                                                       units_group_mode=units_group_mode,
                                                       load_waveforms=load_waveforms, time_slices=time_slices))
        return self.combine_blocks(all_blocks)

    def combine_blocks(self, all_blocks):
        # Note: Everything is loaded with the same parameters //and files have same structure,
        # thus the following is possible.
        # TODO: Do all t_starts and t_stops and time values fit correctly???
        for i in range(1, len(all_blocks)):
            unit_index = 0
            for chidx in all_blocks[i].channel_indexes:
                if chidx.name == 'ChannelIndex for Unit':
                    break
                c = -1
                if chidx.analogsignals:
                    for a, main_chidx in enumerate(all_blocks[0].channel_indexes):
                        if main_chidx.name == chidx.name:
                            c = a
                            break
                    if c == -1:
                        all_blocks[0].channel_indexes.insert(0, chidx)
                    else:
                        # print(all_blocks[0].channel_indexes[c].analogsignals)
                        all_blocks[0].channel_indexes[c].analogsignals.extend(chidx.analogsignals)
                print(c)
            # TODO: Really all Segments corresponding correctly? Should be if no error is raised.

            for seg_ind, seg in enumerate(all_blocks[i].segments):
                all_blocks[0].segments[seg_ind].analogsignals.extend(seg.analogsignals)
                all_blocks[0].segments[seg_ind].epochs.extend(seg.epochs)

        return all_blocks[0]

    class SingleBlackrockIO(BlackrockRawIO, BaseFromRaw):
    
        def __init__(self, filename, nsx_to_load=None, **kargs):
            BlackrockRawIO.__init__(self, filename=filename, nsx_to_load=nsx_to_load, **kargs)
            BaseFromRaw.__init__(self, filename)
