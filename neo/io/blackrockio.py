# -*- coding: utf-8 -*-

import os

import time

from neo.io.basefromrawio import BaseFromRaw
from neo.rawio.blackrockrawio import BlackrockRawIO


class BlackrockIO:
    name = 'Blackrock IO'
    description = "This IO reads .nev/.nsX file of the Blackrock " + \
                  "(Cerebus) recordings system."

    _prefered_signal_group_mode = 'split-all'

    _nev_only = False

    def __init__(self, filename, nsx_to_load=None, nev_only=False, **kargs):
        self._instances = {}
        if nev_only:
            if nsx_to_load is not None:
                raise ValueError("You cannot specify nsx_to_load while nev_only is True")
            self._nev_only = True
            self._instances['nev'] = self.SingleBlackrockIO(filename, nsx_to_load=None,
                                                            nsx_override=os.devnull, **kargs)
        else:
            # TODO: Enable more Strings here
            if nsx_to_load == 'all':
                start = time.time()
                new_instance = self.SingleBlackrockIO(filename, nsx_to_load=None, **kargs)
                nsx_to_load = new_instance.get_avail_nsx()
                self._instances[max(nsx_to_load)] = new_instance
                print(time.time()-start)
                nsx_to_load.remove(max(nsx_to_load))
            # TODO: Adapt this when default behavior in BlackrockRawIO is changed
            elif nsx_to_load is None or nsx_to_load == 'max_res':
                nsx_to_load = []
                new_instance = self.SingleBlackrockIO(filename, nsx_to_load=None, **kargs)
                curr_nsx = max(new_instance.get_avail_nsx())
                self._instances[curr_nsx] = new_instance
            elif isinstance(nsx_to_load, int):
                nsx_to_load = [nsx_to_load]
            elif not isinstance(nsx_to_load, list):
                raise ValueError("nsx_to_load should be 'all' or of type int or list")

            for nsx_val in nsx_to_load:
                self._instances[nsx_val] = (self.SingleBlackrockIO(filename, nsx_to_load=nsx_val, **kargs))

    def read_block(self, block_index=0, lazy=False, cascade=True, signal_group_mode=None,
                   units_group_mode=None, load_waveforms=False, time_slices=None, nsx_to_load=None):

        if self._nev_only:
            if nsx_to_load is not None:
                raise ValueError("You cannot specify nsx_to_load while nev_only is True. This object only "
                                 "contains nev information")
            return self._instances['nev'].read_block(block_index=block_index, lazy=lazy, cascade=cascade,
                                                     signal_group_mode=signal_group_mode,
                                                     units_group_mode=units_group_mode,
                                                     load_waveforms=load_waveforms,
                                                     time_slices=time_slices)

        if nsx_to_load is None:
            nsx_to_load = [max(list(self._instances))]      # For consistency with BlackrockRawIO default behavior
        elif isinstance(nsx_to_load, int):
            nsx_to_load = [nsx_to_load]
        elif nsx_to_load == 'all':
            nsx_to_load = list(self._instances)
        elif not isinstance(nsx_to_load, list):
            raise ValueError("nsx_to_load should be 'all' or of type int or list")
        nsx_to_load.sort(reverse=True)  # TODO: Note on SpikeTrain t_start and t_stop not exact
        # (rather be sure there was measurement at this time than vaguely adding a bit more information)
        all_blocks = []
        for nsx_val in nsx_to_load:
            all_blocks.append(self._instances[nsx_val].read_block(block_index=block_index, lazy=lazy, cascade=cascade,
                                                                  signal_group_mode=signal_group_mode,
                                                                  units_group_mode=units_group_mode,
                                                                  load_waveforms=(not all_blocks and load_waveforms),
                                                                  time_slices=time_slices))
        return self.combine_blocks(all_blocks)

    def combine_blocks(self, all_blocks):

        # Note: Everything is loaded with the same parameters //and files have same structure,
        # thus the following is possible.
        # Merge (from class Container) does not do what is needed, it also merges AnalogSignals etc.,
        # which is not possible here

        # TODO: Do all t_starts and t_stops and time values fit correctly???
        # TODO: Need to find out, how to check, but t_start and t_stop of Analogsignals are correct
        # TODO: SHOULD BE OKAY
        # TODO: !!!CHECK WITH VERSION 2.1!!! 0 for all, because it is not known! CORRECT
        # //TODO: Check if upwards connection is correct everywhere!!! Should be okay!

        for i in range(1, len(all_blocks)):
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
            # => Look at t_starts and t_stops
            # //TODO: Check if create_many_to_one_relationship() is the correct way here, seems to work
            for seg_ind, seg in enumerate(all_blocks[i].segments):
                all_blocks[0].segments[seg_ind].analogsignals.extend(seg.analogsignals)
                # all_blocks[0].segments[seg_ind].epochs.extend(seg.epochs)       # TODO: Where do epochs come from?
        all_blocks[0].create_many_to_one_relationship(force=True)
        return all_blocks[0]

    def get_avail_nsx(self, filename, nsx_override=None):
        if nsx_override is not None:
            filename = nsx_override
        # Avoiding duplicate functionality
        raise NotImplementedError("This functionality is only available for instances of SingleBlackrockIO")



    class SingleBlackrockIO(BlackrockRawIO, BaseFromRaw):

        def __init__(self, filename, nsx_to_load=None, **kargs):
            BlackrockRawIO.__init__(self, filename=filename, nsx_to_load=nsx_to_load, **kargs)
            BaseFromRaw.__init__(self, filename)

        def get_avail_nsx(self):
            return self._avail_nsx
